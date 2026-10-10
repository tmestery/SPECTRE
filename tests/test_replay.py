from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from spectre.bus.store import FindingsBus
from spectre.research.replay import iter_replay_events, load_session_events, replay_session
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import Finding, FindingType


@pytest.fixture
async def session_bus(tmp_path):
    session_id = "eng_replay"
    bus = FindingsBus(tmp_path / session_id / "events.db")
    await bus.connect()
    base = datetime(2026, 6, 25, 12, 0, 0, tzinfo=timezone.utc)
    events = [
        BusEvent(
            type=EventType.ENGAGEMENT_STARTED,
            session_id=session_id,
            timestamp=base,
            payload={"repo": "tmestery/SPECTRE"},
        ),
        BusEvent(
            type=EventType.AGENT_ACTIVATED,
            session_id=session_id,
            timestamp=base + timedelta(seconds=2),
            payload={"agent": "recon"},
        ),
        BusEvent.finding_event(
            session_id,
            Finding(
                type=FindingType.REPOSITORY,
                agent="recon",
                target="tmestery/SPECTRE",
                title="mapped",
            ),
        ),
        BusEvent(
            type=EventType.HANDOFF_DECISION,
            session_id=session_id,
            timestamp=base + timedelta(seconds=6),
            payload={"rule": "repo_mapped", "from_agent": "recon", "to_agent": "vuln_hunter"},
        ),
        BusEvent(
            type=EventType.ENGAGEMENT_COMPLETE,
            session_id=session_id,
            timestamp=base + timedelta(seconds=8),
            payload={"status": "complete"},
        ),
    ]
    events[2].timestamp = base + timedelta(seconds=4)
    for event in events:
        await bus.publish(event)
    yield tmp_path, session_id, bus
    await bus.close()


@pytest.mark.asyncio
async def test_replay_preserves_event_sequence(session_bus):
    data_dir, session_id, _bus = session_bus
    emitted = await replay_session(data_dir, session_id, speed=0.0)
    types = [e.type for e in emitted]
    assert types == [
        EventType.ENGAGEMENT_STARTED,
        EventType.AGENT_ACTIVATED,
        EventType.FINDING,
        EventType.HANDOFF_DECISION,
        EventType.ENGAGEMENT_COMPLETE,
    ]
    assert [e.sequence_num for e in emitted] == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_replay_unknown_session_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="session not found"):
        await load_session_events(tmp_path, "eng_missing")


@pytest.mark.asyncio
async def test_replay_empty_session_raises(tmp_path):
    session_id = "eng_empty"
    bus = FindingsBus(tmp_path / session_id / "events.db")
    await bus.connect()
    await bus.close()
    with pytest.raises(ValueError, match="no events"):
        await load_session_events(tmp_path, session_id)


@pytest.mark.asyncio
async def test_replay_rejects_negative_speed():
    with pytest.raises(ValueError, match="speed"):
        async for _ in iter_replay_events([], speed=-1):
            pass


@pytest.mark.asyncio
async def test_replay_does_not_invoke_tools(session_bus, monkeypatch):
    data_dir, session_id, _bus = session_bus
    github = MagicMock(side_effect=AssertionError("GitHubClient must not be used in replay"))
    gitleaks = MagicMock(side_effect=AssertionError("GitleaksScanner must not be used in replay"))
    monkeypatch.setattr("spectre.tools.github.GitHubClient", github)
    monkeypatch.setattr("spectre.tools.gitleaks.GitleaksScanner", gitleaks)

    emitted = await replay_session(data_dir, session_id, speed=0.0)
    assert len(emitted) == 5
    github.assert_not_called()
    gitleaks.assert_not_called()
