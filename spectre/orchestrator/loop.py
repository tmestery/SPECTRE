import logging
import shutil
from pathlib import Path

from spectre.bus.store import FindingsBus
from spectre.config import settings
from spectre.orchestrator.handoffs import HandoffEngine
from spectre.orchestrator.registry import AgentRegistry
from spectre.research.metrics import export_session_metrics
from spectre.safety.halt import clear_halt, is_halt_requested
from spectre.safety.scope import ScopeEnforcer
from spectre.schemas.engagement import Engagement, EngagementResult, EngagementStatus
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.scope import RepoScope

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, bus: FindingsBus, registry: AgentRegistry | None = None) -> None:
        self.bus = bus
        self.registry = registry or AgentRegistry()
        self._halted: set[str] = set()

    def request_halt(self, engagement_id: str) -> None:
        self._halted.add(engagement_id)

    def is_halted(self, engagement_id: str) -> bool:
        return engagement_id in self._halted

    async def run(self, engagement: Engagement) -> EngagementResult:
        enforcer = ScopeEnforcer(engagement.scope)
        enforcer.check_repo(engagement.repo)
        enforcer.check_branch(engagement.branch)

        engagement.status = EngagementStatus.RUNNING
        handoffs = HandoffEngine(engagement.scope)

        await self.bus.publish(
            BusEvent(
                type=EventType.ENGAGEMENT_STARTED,
                session_id=engagement.id,
                payload={
                    "engagement_id": engagement.id,
                    "repo": engagement.repo,
                    "branch": engagement.branch,
                    "scope": engagement.scope.model_dump(),
                },
            )
        )

        current_agent = "recon"
        while engagement.status == EngagementStatus.RUNNING:
            if self.is_halted(engagement.id) or is_halt_requested(engagement.id):
                engagement.halt_requested = True
                engagement.status = EngagementStatus.HALTED
                await self.bus.publish(
                    BusEvent(
                        type=EventType.ENGAGEMENT_HALTED,
                        session_id=engagement.id,
                        payload={"reason": "kill switch"},
                    )
                )
                break

            result = await self.registry.run_agent(current_agent, engagement, self.bus)

            if settings.judges_enabled and current_agent in {"vuln_hunter", "exploiter"}:
                await self._run_judge(
                    "finding_judge",
                    engagement,
                    reason=f"Advisory batch review after {current_agent}.",
                )

            decision = await handoffs.evaluate(self.bus, current_agent, result, engagement)
            await handoffs.publish(self.bus, engagement.id, decision)

            if settings.judges_enabled:
                await self._run_judge(
                    "handoff_judge",
                    engagement,
                    reason=f"Advisory review of handoff `{decision.rule}`.",
                )

            if decision.to_agent is None:
                if settings.judges_enabled and current_agent == "reporter":
                    await self._run_judge(
                        "report_judge",
                        engagement,
                        reason="Advisory review of report sections.",
                    )
                break
            current_agent = decision.to_agent

        if engagement.status == EngagementStatus.RUNNING:
            engagement.status = EngagementStatus.COMPLETE

        if engagement.workspace_path:
            shutil.rmtree(engagement.workspace_path, ignore_errors=True)
            engagement.workspace_path = None

        clear_halt(engagement.id)

        findings = await self.bus.all_findings()
        await self.bus.publish(
            BusEvent(
                type=EventType.ENGAGEMENT_COMPLETE,
                session_id=engagement.id,
                payload={
                    "status": engagement.status.value,
                    "findings_count": len(findings),
                },
            )
        )

        session_dir = Path(settings.spectre_data_dir) / engagement.id
        try:
            await export_session_metrics(self.bus, engagement.id, session_dir)
        except (ValueError, OSError):
            logger.exception("Failed to export coordination metrics for %s", engagement.id)

        return EngagementResult(
            engagement_id=engagement.id,
            status=engagement.status,
            findings_count=len(findings),
            message=f"Engagement {engagement.status.value}",
        )

    async def _run_judge(self, agent_id: str, engagement: Engagement, *, reason: str) -> None:
        """Run an advisory judge; never alters handoff destinations."""
        await self.bus.publish(
            BusEvent(
                type=EventType.AGENT_MESSAGE,
                session_id=engagement.id,
                payload={
                    "agent": "orchestrator",
                    "message": f"Scheduling {agent_id}: {reason}",
                },
            )
        )
        try:
            await self.registry.run_agent(agent_id, engagement, self.bus)
        except Exception:
            logger.exception("Advisory judge %s failed; continuing engagement", agent_id)


def create_engagement(repo: str, branch: str, scope: RepoScope) -> Engagement:
    return Engagement(
        repo=repo,
        branch=branch,
        scope=scope,
        max_duration_minutes=scope.max_duration_minutes,
    )
