import json
from pathlib import Path

import pytest

from spectre.bus.store import FindingsBus
from spectre.orchestrator.loop import create_engagement
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.scope import RepoScope
from spectre.server.control import SpectreControlServer
from spectre.sessions import session_exists


@pytest.fixture
def scope() -> RepoScope:
    return RepoScope(
        name="test-scope",
        allowed_repos=["tmestery/SPECTRE"],
        allowed_branches=["main"],
    )


class FakeWebSocket:
    def __init__(self) -> None:
        self.sent: list[str] = []
        self.closed = False

    async def send(self, message: str) -> None:
        self.sent.append(message)

    async def close(self) -> None:
        self.closed = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


@pytest.fixture
def scope_file(tmp_path: Path) -> Path:
    RepoScope(
        name="test-scope",
        allowed_repos=["tmestery/SPECTRE"],
        allowed_branches=["main"],
    )
    scope_dir = tmp_path / "scopes"
    scope_dir.mkdir()
    path = scope_dir / "test.yaml"
    path.write_text(
        "name: test-scope\nallowed_repos:\n  - tmestery/SPECTRE\nallowed_branches:\n  - main\n",
        encoding="utf-8",
    )
    return scope_dir


@pytest.mark.asyncio
async def test_control_server_rejects_start_without_github_token(tmp_path, monkeypatch, scope_file):
    from spectre import config

    monkeypatch.setattr(config.settings, "spectre_data_dir", tmp_path / "sessions")
    monkeypatch.setattr(config.settings, "github_token", "")
    server = SpectreControlServer(scope_dir=scope_file)
    ws = FakeWebSocket()

    await server._start_engagement(
        ws,
        repo="tmestery/SPECTRE",
        branch="main",
        scope_path=str(scope_file / "test.yaml"),
    )

    payload = json.loads(ws.sent[-1])
    assert payload["type"] == "error"
    assert "GITHUB_TOKEN" in payload["message"]


@pytest.mark.asyncio
async def test_control_server_rejects_out_of_scope_repo(tmp_path, monkeypatch, scope_file):
    from spectre import config

    monkeypatch.setattr(config.settings, "spectre_data_dir", tmp_path / "sessions")
    monkeypatch.setattr(config.settings, "github_token", "ghp_test")
    server = SpectreControlServer(scope_dir=scope_file)
    ws = FakeWebSocket()

    await server._handler(ws)
    await server._handle_message(
        ws,
        {
            "type": "start_engagement",
            "repo": "octocat/Hello-World",
            "branch": "main",
            "scope_path": str(scope_file / "test.yaml"),
        },
    )

    payloads = [json.loads(message) for message in ws.sent]
    assert any(item["type"] == "error" for item in payloads)


@pytest.mark.asyncio
async def test_control_server_halt_requires_existing_session(tmp_path, monkeypatch):
    from spectre import config

    monkeypatch.setattr(config.settings, "spectre_data_dir", tmp_path / "sessions")
    server = SpectreControlServer(scope_dir=tmp_path / "scopes")
    ws = FakeWebSocket()

    await server._halt(ws, "eng_missing")
    payload = json.loads(ws.sent[-1])
    assert payload["type"] == "error"


@pytest.mark.asyncio
async def test_control_server_subscribe_replays_events(tmp_path, monkeypatch, scope):
    from spectre import config

    data_dir = tmp_path / "sessions"
    monkeypatch.setattr(config.settings, "spectre_data_dir", data_dir)
    engagement = create_engagement("tmestery/SPECTRE", "main", scope)
    bus = FindingsBus(data_dir / engagement.id / "events.db")
    await bus.connect()
    await bus.publish(
        BusEvent(
            type=EventType.AGENT_MESSAGE,
            session_id=engagement.id,
            payload={"agent": "recon", "message": "mapping repo"},
        )
    )
    await bus.close()

    server = SpectreControlServer(scope_dir=tmp_path / "scopes")
    ws = FakeWebSocket()
    await server._subscribe(ws, engagement.id)

    payloads = [json.loads(message) for message in ws.sent]
    assert any(item.get("type") == "agent_message" for item in payloads)
    assert session_exists(data_dir, engagement.id)


def test_control_server_rejects_scope_outside_scope_dir(tmp_path):
    scope_dir = tmp_path / "scopes"
    scope_dir.mkdir()
    outside = tmp_path / "outside.yaml"
    outside.write_text("name: bad\nallowed_repos:\n  - a/b\n", encoding="utf-8")
    server = SpectreControlServer(scope_dir=scope_dir)
    with pytest.raises(ValueError, match="scope path must be under"):
        server._load_scope(str(outside))
