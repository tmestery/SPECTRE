from dataclasses import dataclass


@dataclass(frozen=True)
class LLMRoute:
    model: str
    temperature: float
    json_mode: bool = False


class LLMRouter:
    """Routes subagent tasks to model parameters."""

    TASK_ROUTES: dict[str, LLMRoute] = {
        "surface_analysis": LLMRoute(model="", temperature=0.2, json_mode=True),
        "secret_triage": LLMRoute(model="", temperature=0.1, json_mode=True),
        "cve_prioritization": LLMRoute(model="", temperature=0.1, json_mode=True),
        "threat_mapping": LLMRoute(model="", temperature=0.2, json_mode=True),
        "validation_review": LLMRoute(model="", temperature=0.1, json_mode=True),
        "executive_summary": LLMRoute(model="", temperature=0.4, json_mode=True),
        "agent_routing": LLMRoute(model="", temperature=0.0, json_mode=True),
    }

    def __init__(self, default_model: str) -> None:
        self.default_model = default_model

    def route(self, task: str) -> LLMRoute:
        base = self.TASK_ROUTES.get(task, LLMRoute(model="", temperature=0.2))
        model = base.model or self.default_model
        return LLMRoute(model=model, temperature=base.temperature, json_mode=base.json_mode)
