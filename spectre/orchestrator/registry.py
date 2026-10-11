from uuid import uuid4

from spectre.agents.base import AgentContext
from spectre.agents.cognitive import get_cognitive_runtime
from spectre.agents.exploiter.agent import ExploiterAgent
from spectre.agents.finding_judge.agent import FindingJudgeAgent
from spectre.agents.handoff_judge.agent import HandoffJudgeAgent
from spectre.agents.recon.agent import ReconAgent
from spectre.agents.report_judge.agent import ReportJudgeAgent
from spectre.agents.reporter.agent import ReporterAgent
from spectre.agents.routing.registry import CognitiveRuntime
from spectre.agents.vuln_hunter.agent import VulnHunterAgent
from spectre.bus.store import FindingsBus
from spectre.llm.client import LLMClient
from spectre.schemas.engagement import AgentResult, Engagement
from spectre.schemas.events import BusEvent, EventType


class AgentRegistry:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self._cognitive = CognitiveRuntime.create(llm) if llm else get_cognitive_runtime()
        self._agents = {
            "recon": ReconAgent(self._cognitive),
            "vuln_hunter": VulnHunterAgent(self._cognitive),
            "exploiter": ExploiterAgent(self._cognitive),
            "reporter": ReporterAgent(self._cognitive),
            "finding_judge": FindingJudgeAgent(self._cognitive),
            "handoff_judge": HandoffJudgeAgent(self._cognitive),
            "report_judge": ReportJudgeAgent(self._cognitive),
        }

    def get(self, agent_id: str):
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
