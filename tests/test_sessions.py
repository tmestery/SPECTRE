
import pytest

from spectre.bus.store import FindingsBus
from spectre.orchestrator.loop import create_engagement
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.scope import RepoScope
from spectre.sessions import list_sessions, session_exists


@pytest.fixture
def scope() -> RepoScope:
    return RepoScope(
        name="test-scope",
        allowed_repos=["tmestery/SPECTRE"],
        allowed_branches=["main"],
    )


@pytest.mark.asyncio
async def test_list_sessions_returns_completed_engagement(tmp_path, scope):
    engagement = create_engagement("tmestery/SPECTRE", "main", scope)
    session_dir = tmp_path / engagement.id
    bus = FindingsBus(session_dir / "events.db")
    await bus.connect()
    await bus.publish(
        BusEvent(
            type=EventType.ENGAGEMENT_STARTED,
            session_id=engagement.id,
            payload={
                "repo": engagement.repo,
                "branch": engagement.branch,
                "scope": engagement.scope.model_dump(),
            },
        )
    )
    await bus.publish(
        BusEvent(
            type=EventType.ENGAGEMENT_COMPLETE,
            session_id=engagement.id,
            payload={"status": "complete", "findings_count": 0},
        )
    )
    await bus.close()

    summaries = await list_sessions(tmp_path)
    assert len(summaries) == 1
    assert summaries[0].session_id == engagement.id
    assert summaries[0].status == "complete"


def test_session_exists_false_for_missing(tmp_path):
    assert not session_exists(tmp_path, "eng_missing")


def test_session_exists_true_when_db_present(tmp_path):
    session_dir = tmp_path / "eng_present"
    session_dir.mkdir()
    (session_dir / "events.db").write_text("", encoding="utf-8")
    assert session_exists(tmp_path, "eng_present")


@pytest.mark.asyncio
async def test_list_sessions_ignores_dirs_without_started_event(tmp_path, scope):
    session_dir = tmp_path / "eng_empty"
    session_dir.mkdir()
    bus = FindingsBus(session_dir / "events.db")
    await bus.connect()
    await bus.close()
    assert await list_sessions(tmp_path) == []
