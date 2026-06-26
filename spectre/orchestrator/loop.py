from datetime import datetime, timezone
import shutil
from pathlib import Path
from spectre.orchestrator.handoffs import HandoffEngine
from spectre.orchestrator.registry import AgentRegistry
from spectre.schemas.engagement import Engagement, EngagementResult, EngagementStatus
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.scope import RepoScope
from spectre.safety.scope import ScopeEnforcer


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
            if self.is_halted(engagement.id):
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
            decision = await handoffs.evaluate(self.bus, current_agent, result, engagement)
            await handoffs.publish(self.bus, engagement.id, decision)

            if decision.to_agent is None:
                break
            current_agent = decision.to_agent

        if engagement.status == EngagementStatus.RUNNING:
            engagement.status = EngagementStatus.COMPLETE

        if engagement.workspace_path:
            shutil.rmtree(engagement.workspace_path, ignore_errors=True)
            engagement.workspace_path = None

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

        return EngagementResult(
            engagement_id=engagement.id,
            status=engagement.status,
            findings_count=len(findings),
            message=f"Engagement {engagement.status.value}",
        )


def create_engagement(repo: str, branch: str, scope: RepoScope) -> Engagement:
    return Engagement(
        repo=repo,
        branch=branch,
        scope=scope,
        max_duration_minutes=scope.max_duration_minutes,
    )
