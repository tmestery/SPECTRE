from dataclasses import dataclass, field
from typing import Any, Literal

LLMRole = Literal["system", "user", "assistant"]


@dataclass
class LLMMessage:
    role: LLMRole
    content: str


@dataclass
class LLMCompletionResult:
    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_ms: int = 0


@dataclass
class SubagentResult:
    subagent_id: str
    parent_agent: str
    messages: list[str] = field(default_factory=list)
    findings: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: Literal["complete", "skipped", "failed"] = "complete"
