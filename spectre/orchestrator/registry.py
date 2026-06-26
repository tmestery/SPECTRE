from uuid import uuid4

from spectre.agents.base import AgentContext, BaseAgent
from spectre.agents.exploiter.agent import ExploiterAgent
from spectre.agents.recon.agent import ReconAgent
from spectre.agents.reporter.agent import ReporterAgent
from spectre.agents.vuln_hunter.agent import VulnHunterAgent
from spectre.bus.store import FindingsBus
from spectre.schemas.engagement import AgentResult, Engagement
from spectre.schemas.events import BusEvent, EventType


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {
            "recon": ReconAgent(),
            "vuln_hunter": VulnHunterAgent(),
            "exploiter": ExploiterAgent(),
            "reporter": ReporterAgent(),
        }

    def get(self, agent_id: str) -> BaseAgent:
        if agent_id not in self._agents:
            raise KeyError(f"unknown agent: {agent_id}")
        return self._agents[agent_id]

    async def run_agent(
        self,
        agent_id: str,
        engagement: Engagement,
        bus: FindingsBus,
    ) -> AgentResult:
        agent = self.get(agent_id)
        activation_id = f"act_{uuid4().hex[:8]}"
        ctx = AgentContext(
            engagement_id=engagement.id,
            session_id=engagement.id,
            scope=engagement.scope,
            repo=engagement.repo,
            branch=engagement.branch,
            agent_id=agent_id,
            activation_id=activation_id,
            iteration=1,
            max_iterations=agent.max_iterations,
            workspace_path=engagement.workspace_path,
        )
        await bus.publish(
            BusEvent(
                type=EventType.AGENT_ACTIVATED,
                session_id=engagement.id,
                payload={
                    "agent": agent_id,
                    "activation_id": activation_id,
                    "repo": engagement.repo,
                    "branch": engagement.branch,
                },
            )
        )
        return await agent.run(ctx, bus, engagement=engagement)
