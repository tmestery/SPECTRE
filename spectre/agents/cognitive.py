from spectre.agents.routing.registry import CognitiveRuntime
from spectre.agents.routing.router import AgentCognitiveRouter
from spectre.llm.client import LLMClient
from spectre.schemas.finding import Finding

__all__ = [
    "AgentCognitiveRouter",
    "CognitiveRuntime",
    "LLMClient",
    "finding_to_context",
    "get_cognitive_runtime",
]


_runtime: CognitiveRuntime | None = None


def get_cognitive_runtime() -> CognitiveRuntime:
    global _runtime
    if _runtime is None:
        _runtime = CognitiveRuntime.create()
    return _runtime


def finding_to_context(finding: Finding) -> dict:
    return {
        "id": finding.id,
        "type": finding.type.value,
        "title": finding.title,
        "severity": finding.severity.value,
        "confidence": finding.confidence,
        "target": finding.target,
        "description": finding.description,
        "evidence": finding.evidence,
        "status": finding.status.value,
    }
