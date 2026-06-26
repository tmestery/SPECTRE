from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from spectre.schemas.finding import Finding


class EventType(str, Enum):
    ENGAGEMENT_STARTED = "engagement_started"
    AGENT_ACTIVATED = "agent_activated"
    AGENT_MESSAGE = "agent_message"
    FINDING = "finding"
    HANDOFF_DECISION = "handoff_decision"
    TOOL_INVOCATION = "tool_invocation"
    LLM_INVOCATION = "llm_invocation"
    SUBAGENT_ACTIVATED = "subagent_activated"
    ENGAGEMENT_HALTED = "engagement_halted"
    REPORT_SECTION = "report_section"
    ENGAGEMENT_COMPLETE = "engagement_complete"


class BusEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"evt_{uuid4().hex[:12]}")
    type: EventType
    session_id: str
    sequence_num: int = 0
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def finding_event(cls, session_id: str, finding: Finding) -> "BusEvent":
        return cls(
            type=EventType.FINDING,
            session_id=session_id,
            payload={"finding": finding.model_dump(mode="json")},
        )

    @classmethod
    def agent_message(
        cls,
        session_id: str,
        agent: str,
        message: str,
        *,
        subagent: str | None = None,
    ) -> "BusEvent":
        payload: dict[str, Any] = {"agent": agent, "message": message}
        if subagent:
            payload["subagent"] = subagent
        return cls(
            type=EventType.AGENT_MESSAGE,
            session_id=session_id,
            payload=payload,
        )
