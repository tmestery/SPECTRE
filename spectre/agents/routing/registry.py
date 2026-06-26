from spectre.agents.routing.router import AgentCognitiveRouter, SubagentRegistry
from spectre.llm.client import LLMClient


class CognitiveRuntime:
    def __init__(self, llm: LLMClient, router: AgentCognitiveRouter) -> None:
        self.llm = llm
        self.router = router

    @classmethod
    def create(cls, llm: LLMClient | None = None) -> "CognitiveRuntime":
        client = llm or LLMClient.from_settings()
        router = AgentCognitiveRouter(client, SubagentRegistry())
        return cls(client, router)

    @property
    def available(self) -> bool:
        return self.llm.available
