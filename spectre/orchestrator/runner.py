import asyncio
from dataclasses import dataclass

from spectre.bus.store import FindingsBus
from spectre.orchestrator.loop import Orchestrator
from spectre.safety.halt import clear_halt, is_halt_requested
from spectre.schemas.engagement import Engagement, EngagementResult


@dataclass
class EngagementRunHandle:
    engagement: Engagement
    bus: FindingsBus
    orchestrator: Orchestrator
    task: asyncio.Task[EngagementResult]


async def run_engagement(
    engagement: Engagement,
    bus: FindingsBus,
    orchestrator: Orchestrator | None = None,
) -> EngagementResult:
    crew = orchestrator or Orchestrator(bus)
    return await crew.run(engagement)


def launch_engagement(
    engagement: Engagement,
    bus: FindingsBus,
    orchestrator: Orchestrator | None = None,
) -> EngagementRunHandle:
    crew = orchestrator or Orchestrator(bus)
    task = asyncio.create_task(run_engagement(engagement, bus, crew))
    return EngagementRunHandle(engagement=engagement, bus=bus, orchestrator=crew, task=task)


async def watch_halt_signal(
    session_id: str,
    orchestrator: Orchestrator,
    *,
    poll_interval: float = 0.2,
) -> None:
    while True:
        if is_halt_requested(session_id):
            orchestrator.request_halt(session_id)
            return
        await asyncio.sleep(poll_interval)


async def finalize_engagement(handle: EngagementRunHandle) -> EngagementResult:
    result = await handle.task
    clear_halt(handle.engagement.id)
    return result
