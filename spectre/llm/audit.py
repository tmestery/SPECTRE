from typing import Any

from spectre.bus.store import FindingsBus
from spectre.schemas.events import BusEvent, EventType


async def audit_llm(
    bus: FindingsBus,
    session_id: str,
    *,
    provider: str,
    model: str,
    subagent: str | None,
    parent_agent: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_ms: int,
    status: str,
    metadata: dict[str, Any] | None = None,
) -> BusEvent:
    payload = {
        "provider": provider,
        "model": model,
        "parent_agent": parent_agent,
        "subagent": subagent,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "duration_ms": duration_ms,
        "status": status,
        "metadata": metadata or {},
    }
    return await bus.publish(
        BusEvent(type=EventType.LLM_INVOCATION, session_id=session_id, payload=payload)
    )
