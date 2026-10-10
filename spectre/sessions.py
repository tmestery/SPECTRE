from dataclasses import dataclass
from pathlib import Path

from spectre.bus.store import FindingsBus
from spectre.schemas.events import EventType


@dataclass
class SessionSummary:
    session_id: str
    repo: str
    branch: str
    scope_name: str
    status: str
    updated_at: str


def session_db_path(data_dir: Path, session_id: str) -> Path:
    return data_dir / session_id / "events.db"


def session_exists(data_dir: Path, session_id: str) -> bool:
    return session_db_path(data_dir, session_id).exists()


async def load_session_summary(data_dir: Path, session_id: str) -> SessionSummary | None:
    db_path = session_db_path(data_dir, session_id)
    if not db_path.exists():
        return None

    bus = FindingsBus(db_path)
    await bus.connect()
    try:
        events = await bus.all_events()
        started = next((e for e in events if e.type == EventType.ENGAGEMENT_STARTED), None)
        if not started:
            return None

        status = "running"
        for event in reversed(events):
            if event.type == EventType.ENGAGEMENT_COMPLETE:
                status = "complete"
                break
            if event.type == EventType.ENGAGEMENT_HALTED:
                status = "halted"
                break

        scope = started.payload.get("scope", {})
        updated = events[-1].timestamp if events else started.timestamp
        return SessionSummary(
            session_id=session_id,
            repo=str(started.payload.get("repo", "")),
            branch=str(started.payload.get("branch", "main")),
            scope_name=str(scope.get("name", "")),
            status=status,
            updated_at=updated.isoformat(),
        )
    finally:
        await bus.close()


async def list_sessions(data_dir: Path) -> list[SessionSummary]:
    if not data_dir.exists():
        return []

    summaries: list[SessionSummary] = []
    for session_dir in data_dir.iterdir():
        if not session_dir.is_dir():
            continue
        summary = await load_session_summary(data_dir, session_dir.name)
        if summary:
            summaries.append(summary)

    summaries.sort(key=lambda item: item.updated_at, reverse=True)
    return summaries
