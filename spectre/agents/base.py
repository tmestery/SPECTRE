from spectre.schemas.engagement import AgentResult, AgentResultStatus
from spectre.schemas.scope import RepoScope

AGENT_IDS = ("recon", "vuln_hunter", "exploiter", "reporter")


class AgentContext:
    def __init__(
        self,
        *,
        engagement_id: str,
        session_id: str,
        scope: RepoScope,
        repo: str,
        branch: str,
        agent_id: str,
        activation_id: str,
        iteration: int,
        max_iterations: int,
    ) -> None:
        self.engagement_id = engagement_id
        self.session_id = session_id
        self.scope = scope
        self.repo = repo
        self.branch = branch
        self.agent_id = agent_id
        self.activation_id = activation_id
        self.iteration = iteration
        self.max_iterations = max_iterations


class BaseAgent:
    id: str = "base"
    max_iterations: int = 1

    async def run(self, ctx: AgentContext, bus, **deps) -> AgentResult:  # noqa: ANN001
        raise NotImplementedError


class StubAgent(BaseAgent):
    def __init__(self, agent_id: str, label: str) -> None:
        self.id = agent_id
        self.label = label
        self.max_iterations = 1

    async def run(self, ctx: AgentContext, bus, **deps) -> AgentResult:  # noqa: ANN001
        from spectre.schemas.events import BusEvent

        await bus.publish(
            BusEvent.agent_message(
                ctx.session_id,
                self.id,
                f"{self.label} is not implemented yet (Phase 2+). Completing handoff chain.",
            )
        )
        return AgentResult(status=AgentResultStatus.EXHAUSTED, message=f"{self.id} stub complete")
