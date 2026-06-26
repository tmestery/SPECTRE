import asyncio

import pytest

from spectre.bus.store import FindingsBus
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import Finding, FindingType


@pytest.fixture
async def bus(tmp_path):
    instance = FindingsBus(tmp_path / "session" / "events.db")
    await instance.connect()
    yield instance
    await instance.close()


@pytest.mark.asyncio
async def test_publish_and_get_finding(bus):
    finding = Finding(
        type=FindingType.FILE,
        agent="recon",
        target="tmestery/SPECTRE:README.md",
        title="Tracked file",
    )
    await bus.publish(BusEvent.finding_event("session", finding))
    stored = await bus.get_finding(finding.id)
    assert stored is not None
    assert stored.title == "Tracked file"


@pytest.mark.asyncio
async def test_rejects_invalid_finding_payload():
    with pytest.raises(Exception):
        Finding(type=FindingType.FILE, agent="recon", target="x", title="t", confidence=2.0)


@pytest.mark.asyncio
async def test_query_filters_by_type(bus):
    f1 = Finding(type=FindingType.FILE, agent="recon", target="a", title="file")
    f2 = Finding(type=FindingType.WORKFLOW, agent="recon", target="b", title="workflow")
    await bus.publish(BusEvent.finding_event("session", f1))
    await bus.publish(BusEvent.finding_event("session", f2))
    files = await bus.query_findings(finding_type="file")
    assert len(files) == 1
    assert files[0].type == FindingType.FILE


@pytest.mark.asyncio
async def test_subscriber_receives_matching_events(bus):
    received: list[BusEvent] = []

    async def collect():
        async for event in bus.subscribe([EventType.AGENT_MESSAGE]):
            received.append(event)
            break

    task = asyncio.create_task(collect())
    await bus.publish(BusEvent.agent_message("session", "recon", "hello"))
    await task
    assert received[0].payload["message"] == "hello"


@pytest.mark.asyncio
async def test_sequence_numbers_monotonic(bus):
    e1 = await bus.publish(BusEvent(type=EventType.AGENT_MESSAGE, session_id="session", payload={}))
    e2 = await bus.publish(BusEvent(type=EventType.AGENT_MESSAGE, session_id="session", payload={}))
    assert e2.sequence_num > e1.sequence_num
