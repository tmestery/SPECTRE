"""Finding Judge — advisory batch review of secret/CVE/misconfig findings."""

from __future__ import annotations

from spectre.agents.base import AgentContext, AgentResult, AgentResultStatus
from spectre.agents.cognitive import get_cognitive_runtime
from spectre.agents.routing.registry import CognitiveRuntime
from spectre.bus.store import FindingsBus
from spectre.safety.scope import ScopeEnforcer, ScopeViolationError, redact_evidence
from spectre.schemas.events import BusEvent
from spectre.schemas.finding import Finding, FindingType, Severity
from spectre.schemas.judging import JudgmentVerdict, make_judgment_finding

REVIEWABLE_TYPES = {
    FindingType.SECRET,
    FindingType.VULNERABILITY,
    FindingType.MISCONFIGURATION,
}


def repo_slug_from_target(target: str) -> str:
    """Extract owner/repo from finding targets like owner/repo:path."""
    return target.split(":", 1)[0]


class FindingJudgeAgent:
    id = "finding_judge"
    max_iterations = 3

    def __init__(self, cognitive: CognitiveRuntime | None = None) -> None:
        self._cognitive = cognitive or get_cognitive_runtime()

    async def run(self, ctx: AgentContext, bus: FindingsBus, engagement=None, **deps) -> AgentResult:
        enforcer = ScopeEnforcer(ctx.scope)
        try:
            enforcer.check_repo(ctx.repo)
        except ScopeViolationError as exc:
            await bus.publish(
                BusEvent.agent_message(ctx.session_id, self.id, f"Scope rejected: {exc}")
            )
            return AgentResult(status=AgentResultStatus.BLOCKED, message=str(exc))

        findings = await bus.all_findings()
        already_reviewed = {
            f.evidence.get("reviewed_finding_id")
            for f in findings
            if f.type == FindingType.JUDGMENT and f.evidence.get("reviewed_finding_id")
        }
        reviewable = [
            f
            for f in findings
            if f.type in REVIEWABLE_TYPES and f.id not in already_reviewed
        ]

        if not reviewable:
            await bus.publish(
                BusEvent.agent_message(
                    ctx.session_id,
                    self.id,
                    "No new actionable findings to judge.",
                )
            )
            return AgentResult(status=AgentResultStatus.EXHAUSTED, message="nothing to judge")

        judgments = 0
        skipped_oos = 0
        for finding in reviewable:
            slug = repo_slug_from_target(finding.target)
            if not ctx.scope.allows_repo(slug):
                skipped_oos += 1
                await bus.publish(
                    BusEvent.agent_message(
                        ctx.session_id,
                        self.id,
                        f"Skipping out-of-scope finding {finding.id} ({slug}).",
                    )
                )
                continue

            verdict, rationale = self._deterministic_verdict(finding)
            if self._cognitive.llm.available:
                verdict, rationale = await self._llm_refine(ctx, finding, verdict, rationale)

            judgment = make_judgment_finding(
                agent=self.id,
                target=finding.target,
                reviewed_finding_id=finding.id,
                verdict=verdict,
                rationale=rationale,
                severity=finding.severity if verdict == JudgmentVerdict.UPHOLD else Severity.INFO,
            )
            # Ensure evidence snippets stay redacted if copied later
            judgment.evidence = {
                **judgment.evidence,
                "reviewed_evidence_redacted": redact_evidence(finding.evidence),
            }
            await bus.publish(BusEvent.finding_event(ctx.session_id, judgment))
            judgments += 1

        await bus.publish(
            BusEvent.agent_message(
                ctx.session_id,
                self.id,
                (
                    f"Batch review complete: {judgments} judgment(s) published"
                    + (f"; skipped {skipped_oos} out-of-scope" if skipped_oos else "")
                    + "."
                ),
            )
        )
        if judgments == 0:
            return AgentResult(status=AgentResultStatus.EXHAUSTED, message="all findings out of scope")
        return AgentResult(
            status=AgentResultStatus.COMPLETE,
            message=f"published {judgments} judgments",
            iterations_used=1,
        )

    def _deterministic_verdict(self, finding: Finding) -> tuple[JudgmentVerdict, str]:
        if finding.type == FindingType.SECRET:
            if finding.confidence >= 0.8:
                return (
                    JudgmentVerdict.UPHOLD,
                    f"High-confidence secret ({finding.confidence:.2f}) with redacted evidence.",
                )
            if finding.confidence < 0.5:
                return (
                    JudgmentVerdict.DISMISS,
                    f"Low-confidence secret ({finding.confidence:.2f}); likely noise.",
                )
            return (
                JudgmentVerdict.DOWNGRADE,
                f"Moderate-confidence secret ({finding.confidence:.2f}); needs stronger validation.",
            )

        if finding.type == FindingType.VULNERABILITY:
            exploitability = float(finding.evidence.get("exploitability", 0) or 0)
            if exploitability >= 0.7:
                return (
                    JudgmentVerdict.UPHOLD,
                    f"CVE looks reachable (exploitability {exploitability:.2f}).",
                )
            return (
                JudgmentVerdict.DOWNGRADE,
                f"CVE exploitability uncertain ({exploitability:.2f}).",
            )

        if finding.type == FindingType.MISCONFIGURATION:
            if finding.severity in {Severity.HIGH, Severity.CRITICAL}:
                return (
                    JudgmentVerdict.UPHOLD,
                    f"High-severity workflow misconfiguration ({finding.severity.value}).",
                )
            return (
                JudgmentVerdict.DOWNGRADE,
                f"Misconfiguration severity {finding.severity.value}; confirm blast radius.",
            )

        return JudgmentVerdict.DISMISS, "Finding type not in judging scope."

    async def _llm_refine(
        self,
        ctx: AgentContext,
        finding: Finding,
        verdict: JudgmentVerdict,
        rationale: str,
    ) -> tuple[JudgmentVerdict, str]:
        """Optional LLM polish; falls back to deterministic on any failure."""
        from spectre.llm.prompts import SPECTRE_SYSTEM
        from spectre.llm.types import LLMMessage

        try:
            data, _completion = await self._cognitive.llm.complete_json(
                [
                    LLMMessage(
                        role="system",
                        content=(
                            f"{SPECTRE_SYSTEM}\nYou are Finding Judge. "
                            "Return JSON: {\"verdict\":\"uphold|downgrade|dismiss\",\"rationale\":\"...\"}. "
                            "Do not invent file paths or CVEs. Advisory only."
                        ),
                    ),
                    LLMMessage(
                        role="user",
                        content=(
                            f"Scope repos: {', '.join(ctx.scope.allowed_repos)}\n"
                            f"Proposed verdict: {verdict.value}\n"
                            f"Proposed rationale: {rationale}\n"
                            f"Finding: id={finding.id} type={finding.type.value} "
                            f"title={finding.title} confidence={finding.confidence} "
                            f"severity={finding.severity.value} "
                            f"evidence={redact_evidence(finding.evidence)}"
                        ),
                    ),
                ],
                temperature=0.1,
            )
            refined = JudgmentVerdict(str(data.get("verdict", verdict.value)))
            text = str(data.get("rationale") or rationale)
            return refined, text
        except (ValueError, KeyError, TypeError, RuntimeError):
            return verdict, rationale
