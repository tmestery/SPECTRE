from dataclasses import dataclass
from datetime import datetime, timezone

from spectre.bus.store import FindingsBus
from spectre.orchestrator.profiles import DEFAULT_PROFILE, HandoffProfile, load_handoff_profile
from spectre.schemas.engagement import AgentResult, AgentResultStatus, Engagement
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import Finding, FindingStatus, FindingType, Severity
from spectre.schemas.scope import RepoScope

# Cap Exploiter → VulnHunter retries to avoid infinite loops.
MAX_VALIDATION_FAILED_RETRIES = 1


@dataclass
class HandoffDecision:
    rule: str
    from_agent: str
    to_agent: str | None
    rationale: str
    input_finding_ids: list[str]


class HandoffEngine:
    def __init__(self, scope: RepoScope, profile: HandoffProfile | None = None) -> None:
        self.scope = scope
        self.profile = profile or DEFAULT_PROFILE

    async def evaluate(
        self,
        bus: FindingsBus,
        from_agent: str,
        result: AgentResult,
        engagement: Engagement,
    ) -> HandoffDecision:
        findings = await bus.all_findings()

        if engagement.halt_requested:
            return HandoffDecision(
                rule="engagement_halted",
                from_agent=from_agent,
                to_agent=None,
                rationale="Engagement halt requested.",
                input_finding_ids=[],
            )

        elapsed_minutes = (datetime.now(timezone.utc) - engagement.started_at).total_seconds() / 60
        if elapsed_minutes > engagement.max_duration_minutes:
            return self._decision(
                "engagement_timeout",
                from_agent,
                "reporter",
                "Engagement time limit reached; generating partial report.",
                [],
            )

        if from_agent == "recon" and result.status in {
            AgentResultStatus.COMPLETE,
            AgentResultStatus.EXHAUSTED,
        }:
            return self._evaluate_recon(findings, from_agent)

        if from_agent == "vuln_hunter":
            return self._evaluate_vuln_hunter(findings, from_agent, result)

        if from_agent == "exploiter":
            return await self._evaluate_exploiter(bus, findings, from_agent, result)

        if from_agent == "reporter":
            return HandoffDecision(
                rule="report_complete",
                from_agent=from_agent,
                to_agent=None,
                rationale="Reporter finished.",
                input_finding_ids=[],
            )

        return HandoffDecision(
            rule="no_transition",
            from_agent=from_agent,
            to_agent=None,
            rationale="No handoff rule matched.",
            input_finding_ids=[],
        )

    def _evaluate_recon(self, findings: list[Finding], from_agent: str) -> HandoffDecision:
        repo_findings = [
            f
            for f in findings
            if f.type == FindingType.REPOSITORY and self.scope.allows_repo(f.target)
        ]
        surface = [
            f
            for f in findings
            if f.type in {FindingType.FILE, FindingType.WORKFLOW, FindingType.DEPENDENCY}
        ]
        if repo_findings and surface:
            ids = [f.id for f in repo_findings + surface[:5]]
            return self._decision(
                "repo_mapped",
                from_agent,
                "vuln_hunter",
                "Recon mapped repo structure with at least one scannable surface.",
                ids,
            )
        return self._decision(
            "recon_exhausted_empty_repo",
            from_agent,
            "reporter",
            "Recon found no scannable repo surface.",
            [f.id for f in repo_findings],
        )

    def _evaluate_vuln_hunter(
        self, findings: list[Finding], from_agent: str, result: AgentResult
    ) -> HandoffDecision:
        actionable = [f for f in findings if self._is_actionable(f)]
        if actionable:
            return self._decision(
                "actionable_finding",
                from_agent,
                "exploiter",
                "VulnHunter found an actionable finding worth validating.",
                [f.id for f in actionable],
            )
        return self._decision(
            "no_actionable_findings",
            from_agent,
            "reporter",
            "VulnHunter found no actionable findings; proceeding to report.",
            [],
        )

    async def _evaluate_exploiter(
        self,
        bus: FindingsBus,
        findings: list[Finding],
        from_agent: str,
        result: AgentResult,
    ) -> HandoffDecision:
        validated = [
            f
            for f in findings
            if f.type == FindingType.VALIDATION_ATTEMPT and f.status == FindingStatus.CONFIRMED
        ]
        if validated:
            return self._decision(
                "finding_validated",
                from_agent,
                "reporter",
                "Exploiter validated at least one finding.",
                [f.id for f in validated],
            )

        false_positives = [
            f
            for f in findings
            if f.type == FindingType.VALIDATION_ATTEMPT
            and f.status == FindingStatus.FALSE_POSITIVE
        ]
        pending_actionable = [
            f for f in findings if f.status == FindingStatus.TENTATIVE and self._is_actionable(f)
        ]
        retry_count = await self._count_validation_failed_retries(bus)
        if (
            false_positives
            and pending_actionable
            and retry_count < MAX_VALIDATION_FAILED_RETRIES
        ):
            return self._decision(
                "validation_failed_retry",
                from_agent,
                "vuln_hunter",
                (
                    "Exploiter marked validations as false positives while actionable "
                    f"findings remain; retrying VulnHunter "
                    f"(attempt {retry_count + 1}/{MAX_VALIDATION_FAILED_RETRIES})."
                ),
                [f.id for f in false_positives[:3] + pending_actionable[:3]],
            )

        reportable = [
            f for f in findings if f.severity in {Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL}
        ]
        if result.status == AgentResultStatus.EXHAUSTED and reportable:
            return self._decision(
                "validations_exhausted",
                from_agent,
                "reporter",
                "Validation attempts exhausted with reportable findings.",
                [f.id for f in reportable[:5]],
            )
        return self._decision(
            "no_validation",
            from_agent,
            "reporter",
            "No validations to report.",
            [],
        )

    async def _count_validation_failed_retries(self, bus: FindingsBus) -> int:
        events = await bus.all_events(types=[EventType.HANDOFF_DECISION])
        return sum(
            1
            for event in events
            if event.payload.get("rule") == "validation_failed_retry"
        )

    def _is_actionable(self, finding: Finding) -> bool:
        if finding.type == FindingType.SECRET:
            return finding.confidence >= self.profile.secret_confidence_min
        if finding.type == FindingType.VULNERABILITY:
            return (
                float(finding.evidence.get("exploitability", 0) or 0)
                >= self.profile.vulnerability_exploitability_min
            )
        if finding.type == FindingType.MISCONFIGURATION:
            return finding.severity in self.profile.misconfig_severity_set()
        return False

    @classmethod
    def from_engagement(cls, engagement: Engagement) -> "HandoffEngine":
        profile = load_handoff_profile(engagement.handoff_profile)
        return cls(engagement.scope, profile)

    def _decision(
        self,
        rule: str,
        from_agent: str,
        to_agent: str | None,
        rationale: str,
        finding_ids: list[str],
    ) -> HandoffDecision:
        return HandoffDecision(
            rule=rule,
            from_agent=from_agent,
            to_agent=to_agent,
            rationale=rationale,
            input_finding_ids=finding_ids,
        )

    async def publish(self, bus: FindingsBus, session_id: str, decision: HandoffDecision) -> None:
        await bus.publish(
            BusEvent(
                type=EventType.HANDOFF_DECISION,
                session_id=session_id,
                payload={
                    "rule": decision.rule,
                    "from_agent": decision.from_agent,
                    "to_agent": decision.to_agent,
                    "rationale": decision.rationale,
                    "input_finding_ids": decision.input_finding_ids,
                },
            )
        )
