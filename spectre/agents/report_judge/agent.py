"""Report Judge — advisory review of report sections for accuracy."""

from __future__ import annotations

import re

from spectre.agents.base import AgentContext, AgentResult, AgentResultStatus
from spectre.agents.cognitive import get_cognitive_runtime
from spectre.agents.routing.registry import CognitiveRuntime
from spectre.bus.store import FindingsBus
from spectre.safety.scope import ScopeEnforcer, ScopeViolationError
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.judging import ReportVerdictPayload, ReportVerdictValue, report_verdict_event

CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)


class ReportJudgeAgent:
    id = "report_judge"
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

        events = await bus.all_events()
        sections = [e for e in events if e.type == EventType.REPORT_SECTION]
        prior = {
            tuple(e.payload.get("report_section_ids") or [])
            for e in events
            if e.type == EventType.REPORT_VERDICT
        }
        section_ids = [str(s.payload.get("section_id") or s.id) for s in sections]
        key = tuple(section_ids)
        if not sections:
            await bus.publish(
                BusEvent.agent_message(ctx.session_id, self.id, "No report sections to review.")
            )
            return AgentResult(status=AgentResultStatus.EXHAUSTED, message="no report sections")
        if key in prior:
            await bus.publish(
                BusEvent.agent_message(ctx.session_id, self.id, "Report already judged.")
            )
            return AgentResult(status=AgentResultStatus.EXHAUSTED, message="already judged")

        findings = await bus.all_findings()
        known_cves = {
            str(f.evidence.get("cve_id") or "").upper()
            for f in findings
            if f.evidence.get("cve_id")
        }
        known_paths = {
            str(f.evidence.get("path") or f.evidence.get("file") or "")
            for f in findings
            if f.evidence.get("path") or f.evidence.get("file")
        }
        known_paths |= {f.target.split(":", 1)[1] for f in findings if ":" in f.target}
        known_paths = {p for p in known_paths if p}

        issues: list[str] = []
        for section in sections:
            markdown = str(section.payload.get("markdown") or "")
            for cve in CVE_RE.findall(markdown):
                if cve.upper() not in known_cves:
                    issues.append(f"Invented or untracked CVE in report: {cve}")
            for path in re.findall(r"`([^`]+/[^`]+)`", markdown):
                if known_paths and path not in known_paths:
                    issues.append(f"Path not present in findings evidence: {path}")

        verdict = ReportVerdictValue.REVISE if issues else ReportVerdictValue.ACCEPT
        rationale = (
            "Report references findings on the bus."
            if not issues
            else "Report contains claims not backed by bus findings."
        )
        await bus.publish(
            report_verdict_event(
                ctx.session_id,
                ReportVerdictPayload(
                    report_section_ids=section_ids,
                    verdict=verdict,
                    issues=issues[:20],
                    rationale=rationale,
                    advisory=True,
                ),
            )
        )
        await bus.publish(
            BusEvent.agent_message(
                ctx.session_id,
                self.id,
                f"Report verdict: {verdict.value} ({len(issues)} issue(s)).",
            )
        )
        return AgentResult(
            status=AgentResultStatus.COMPLETE,
            message=verdict.value,
            iterations_used=1,
        )
