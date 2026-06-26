import time
from typing import Any

from spectre.bus.store import FindingsBus
from spectre.schemas.events import BusEvent, EventType


async def audit_tool(
    bus: FindingsBus,
    session_id: str,
    *,
    tool: str,
    target: str,
    scope_check: str,
    exit_code: int,
    duration_ms: int,
    metadata: dict[str, Any] | None = None,
) -> BusEvent:
    payload = {
        "tool": tool,
        "target": target,
        "scope_check": scope_check,
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "metadata": metadata or {},
    }
    return await bus.publish(
        BusEvent(type=EventType.TOOL_INVOCATION, session_id=session_id, payload=payload)
    )


class AuditTimer:
    def __init__(self) -> None:
        self._start = time.perf_counter()

    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self._start) * 1000)
