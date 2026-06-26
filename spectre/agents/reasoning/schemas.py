from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentAction(BaseModel):
    action: Literal["tool", "message", "complete"]
    reasoning: str = Field(description="Brief rationale shown in the demo UI")
    tool: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None
    handoff_rationale: str | None = None


class ReasoningStep(BaseModel):
    step: int
    action: AgentAction
    tool_result: dict[str, Any] | None = None


class ReasoningResult(BaseModel):
    steps: list[ReasoningStep] = Field(default_factory=list)
    completed: bool = False
    skipped: bool = False
    final_message: str | None = None
    handoff_rationale: str | None = None
    state: dict[str, Any] = Field(default_factory=dict)
