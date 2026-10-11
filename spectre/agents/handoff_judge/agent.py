"""Handoff Judge — advisory review of handoff_decision events."""

from __future__ import annotations

from spectre.agents.base import AgentContext, AgentResult, AgentResultStatus
from spectre.agents.cognitive import get_cognitive_runtime
from spectre.agents.routing.registry import CognitiveRuntime
from spectre.bus.store import FindingsBus
from spectre.safety.scope import ScopeEnforcer, ScopeViolationError
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.judging import (
    HandoffVerdictPayload,
    HandoffVerdictValue,
    handoff_verdict_event,
)


class HandoffJudgeAgent:
    id = "handoff_judge"
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
        decisions = [e for e in events if e.type == EventType.HANDOFF_DECISION]
        prior_verdicts = {
            e.payload.get("decision_id")
            for e in events
            if e.type == EventType.HANDOFF_VERDICT and e.payload.get("decision_id")
        }
        pending = [d for d in decisions if d.id not in prior_verdicts]
        if not pending:
            await bus.publish(
                BusEvent.agent_message(ctx.session_id, self.id, "No new handoffs to review.")
            )
            return AgentResult(status=AgentResultStatus.EXHAUSTED, message="nothing to review")

        published = 0
        for decision in pending:
            verdict, rationale = self._deterministic_verdict(decision.payload)
            payload = HandoffVerdictPayload(
                decision_id=decision.id,
                verdict=verdict,
                rationale=rationale,
                advisory=True,
            )
            await bus.publish(handoff_verdict_event(ctx.session_id, payload))
            published += 1

        await bus.publish(
            BusEvent.agent_message(
                ctx.session_id,
                self.id,
                f"Published {published} advisory handoff verdict(s).",
            )
        )
        return AgentResult(
            status=AgentResultStatus.COMPLETE,
            message=f"published {published} handoff verdicts",
            iterations_used=1,
        )

    def _deterministic_verdict(self, payload: dict) -> tuple[HandoffVerdictValue, str]:
        rule = str(payload.get("rule", ""))
        to_agent = payload.get("to_agent")
        rationale = str(payload.get("rationale") or "")

        if not to_agent and rule not in {"report_complete", "engagement_halted", "no_transition"}:
            return (
                HandoffVerdictValue.DEFER,
                f"Handoff `{rule}` ended the chain without a clear terminal reason.",
            )
        if rule == "validation_failed_retry":
            return (
                HandoffVerdictValue.APPROVE,
                "Bounded retry to VulnHunter is within protocol.",
            )
        if rule in {"repo_mapped", "actionable_finding", "finding_validated"}:
            return (
                HandoffVerdictValue.APPROVE,
                f"Rule `{rule}` matches v1 handoff protocol. {rationale}".strip(),
            )
        if rule in {"no_actionable_findings", "validations_exhausted", "recon_exhausted_empty_repo"}:
            return (
                HandoffVerdictValue.APPROVE,
                f"Terminal/skip path `{rule}` is acceptable for reporting.",
            )
        if to_agent is None:
            return HandoffVerdictValue.APPROVE, f"Terminal handoff `{rule}` acknowledged."
        return (
            HandoffVerdictValue.DEFER,
            f"Unrecognized handoff rule `{rule}`; leaving advisory deferral.",
        )
