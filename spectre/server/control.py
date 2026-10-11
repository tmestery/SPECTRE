import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from websockets.asyncio.server import Server, ServerConnection
from websockets.exceptions import ConnectionClosed

from spectre.bus.store import FindingsBus
from spectre.config import settings
from spectre.github_auth import github_api_error_message, github_token_configured
from spectre.orchestrator.loop import Orchestrator, create_engagement
from spectre.orchestrator.runner import launch_engagement, watch_halt_signal
from spectre.safety.halt import request_halt
from spectre.schemas.scope import RepoScope
from spectre.server.serve import serve_spectre_ws
from spectre.server.websocket import RELAYED_EVENTS
from spectre.sessions import list_sessions, session_exists

logger = logging.getLogger(__name__)


@dataclass
class ScopeOption:
    path: str
    name: str
    allowed_repos: list[str]
    allowed_branches: list[str]


@dataclass
class ActiveEngagement:
    session_id: str
    bus: FindingsBus
    orchestrator: Orchestrator
    task: asyncio.Task
    relay_task: asyncio.Task
    halt_task: asyncio.Task
    subscribers: set[ServerConnection] = field(default_factory=set)


class SpectreControlServer:
    def __init__(self, scope_dir: Path | None = None) -> None:
        self.scope_dir = scope_dir or settings.scope_dir
        self._clients: set[ServerConnection] = set()
        self._active: ActiveEngagement | None = None
        self._server: Server | None = None

    async def start(self) -> Server:
        self._server = await serve_spectre_ws(self._handler, settings.ws_host, settings.ws_port)
        return self._server

    async def run_forever(self) -> None:
        server = await self.start()
        await server.wait_closed()

    async def stop(self) -> None:
        if self._active:
            await self._teardown_active()
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        for client in list(self._clients):
            await client.close()

    async def _handler(self, websocket: ServerConnection) -> None:
        self._clients.add(websocket)
        try:
            await self._send(
                websocket,
                {
                    "type": "server_hello",
                    "defaults": self._defaults(),
                    "scopes": [scope.__dict__ for scope in self._load_scopes()],
                    "active_session": self._active.session_id if self._active else None,
                    "sessions": [summary.__dict__ for summary in await list_sessions(settings.spectre_data_dir)],
                    "github_token_configured": github_token_configured(),
                    "llm_configured": settings.llm_enabled and bool(settings.llm_api_key),
                    "llm_provider": settings.llm_provider,
                    "llm_model": settings.llm_model,
                },
            )
            async for message in websocket:
                await self._handle_message(websocket, json.loads(message))
        finally:
            self._clients.discard(websocket)
            if self._active:
                self._active.subscribers.discard(websocket)

    async def _handle_message(self, websocket: ServerConnection, data: dict[str, Any]) -> None:
        msg_type = data.get("type")
        if msg_type == "start_engagement":
            await self._start_engagement(
                websocket,
                repo=str(data.get("repo", "")),
                branch=str(data.get("branch", "main")),
                scope_path=str(data.get("scope_path", "")),
            )
            return
        if msg_type == "subscribe":
            await self._subscribe(websocket, str(data.get("session_id", "")))
            return
        if msg_type == "halt":
            await self._halt(websocket, str(data.get("session_id", "")))
            return
        if msg_type == "list_sessions":
            await self._send(
                websocket,
                {
                    "type": "sessions_list",
                    "sessions": [
                        summary.__dict__
                        for summary in await list_sessions(settings.spectre_data_dir)
                    ],
                },
            )
            return
        if msg_type == "replay_session":
            await self._replay_session(
                websocket,
                session_id=str(data.get("session_id", "")),
                speed=float(data.get("speed", 0.0)),
            )
            return
        await self._send(websocket, {"type": "error", "message": f"unknown message type: {msg_type}"})

    async def _start_engagement(
        self,
        websocket: ServerConnection,
        *,
        repo: str,
        branch: str,
        scope_path: str,
    ) -> None:
        if self._active:
            await self._send(
                websocket,
                {"type": "error", "message": f"engagement already running: {self._active.session_id}"},
            )
            return

        try:
            scope = self._load_scope(scope_path)
        except (OSError, ValueError) as exc:
            await self._send(websocket, {"type": "error", "message": str(exc)})
            return

        if not scope.allows_repo(repo):
            await self._send(websocket, {"type": "error", "message": f"repo not in scope: {repo}"})
            return
        if not scope.allows_branch(branch):
            await self._send(websocket, {"type": "error", "message": f"branch not in scope: {branch}"})
            return
        if not github_token_configured():
            await self._send(
                websocket,
                {
                    "type": "error",
                    "message": (
                        "GITHUB_TOKEN is not set. Add it to .env before starting an audit "
                        "(e.g. GITHUB_TOKEN=$(gh auth token))."
                    ),
                },
            )
            return

        engagement = create_engagement(repo, branch, scope)
        session_dir = settings.spectre_data_dir / engagement.id
        bus = FindingsBus(session_dir / "events.db")
        await bus.connect()
        orchestrator = Orchestrator(bus)
        handle = launch_engagement(engagement, bus, orchestrator)
        relay_task = asyncio.create_task(self._relay_active_events(engagement.id, bus))
        halt_task = asyncio.create_task(watch_halt_signal(engagement.id, orchestrator))

        self._active = ActiveEngagement(
            session_id=engagement.id,
            bus=bus,
            orchestrator=orchestrator,
            task=handle.task,
            relay_task=relay_task,
            halt_task=halt_task,
            subscribers={websocket},
        )

        async def cleanup() -> None:
            failure_message: str | None = None
            try:
                await handle.task
            except Exception as exc:
                failure_message = github_api_error_message(exc, repo) or str(exc)
            finally:
                if failure_message:
                    await self._notify_subscribers(
                        {
                            "type": "engagement_failed",
                            "session_id": engagement.id,
                            "message": failure_message,
                        }
                    )
                if self._active and self._active.session_id == engagement.id:
                    await self._teardown_active()

        asyncio.create_task(cleanup())

        await self._send(
            websocket,
            {
                "type": "engagement_launched",
                "session_id": engagement.id,
                "repo": repo,
                "branch": branch,
                "scope_path": scope_path,
            },
        )

    async def _replay_session(
        self,
        websocket: ServerConnection,
        *,
        session_id: str,
        speed: float,
    ) -> None:
        from spectre.research.replay import replay_session

        if not session_id:
            await self._send(websocket, {"type": "error", "message": "session_id is required"})
            return
        if self._active:
            await self._send(
                websocket,
                {"type": "error", "message": "cannot replay while an engagement is active"},
            )
            return
        try:
            await self._send(
                websocket,
                {"type": "replay_started", "session_id": session_id, "speed": speed},
            )

            async def on_event(event) -> None:
                await self._send(websocket, event.model_dump(mode="json"))

            events = await replay_session(
                settings.spectre_data_dir,
                session_id,
                speed=speed,
                on_event=on_event,
            )
            await self._send(
                websocket,
                {
                    "type": "replay_complete",
                    "session_id": session_id,
                    "events": len(events),
                },
            )
        except FileNotFoundError:
            await self._send(websocket, {"type": "error", "message": f"session not found: {session_id}"})
        except ValueError as exc:
            await self._send(websocket, {"type": "error", "message": str(exc)})

    async def _subscribe(self, websocket: ServerConnection, session_id: str) -> None:
        if not session_id:
            await self._send(websocket, {"type": "error", "message": "session_id is required"})
            return
        if not session_exists(settings.spectre_data_dir, session_id):
            await self._send(websocket, {"type": "error", "message": f"session not found: {session_id}"})
            return

        db_path = settings.spectre_data_dir / session_id / "events.db"
        bus = FindingsBus(db_path)
        await bus.connect()
        try:
            for event in await bus.all_events(RELAYED_EVENTS):
                await self._send(websocket, event.model_dump(mode="json"))
        finally:
            await bus.close()

        if self._active and self._active.session_id == session_id:
            self._active.subscribers.add(websocket)
            await self._send(websocket, {"type": "subscribed", "session_id": session_id, "live": True})
            return

        await self._send(websocket, {"type": "subscribed", "session_id": session_id, "live": False})

    async def _halt(self, websocket: ServerConnection, session_id: str) -> None:
        if not session_exists(settings.spectre_data_dir, session_id):
            await self._send(websocket, {"type": "error", "message": f"session not found: {session_id}"})
            return

        request_halt(session_id)
        if self._active and self._active.session_id == session_id:
            self._active.orchestrator.request_halt(session_id)

        await self._send(websocket, {"type": "halt_ack", "session_id": session_id})

    async def _relay_active_events(self, session_id: str, bus: FindingsBus) -> None:
        async for event in bus.subscribe(RELAYED_EVENTS):
            if not self._active or self._active.session_id != session_id:
                break
            payload = event.model_dump(mode="json")
            dead: list[ServerConnection] = []
            for client in list(self._active.subscribers):
                try:
                    await self._send(client, payload)
                except ConnectionClosed:
                    dead.append(client)
            for client in dead:
                self._active.subscribers.discard(client)

    async def _notify_subscribers(self, payload: dict[str, Any]) -> None:
        if not self._active:
            return
        dead: list[ServerConnection] = []
        for client in list(self._active.subscribers):
            try:
                await self._send(client, payload)
            except ConnectionClosed:
                dead.append(client)
        for client in dead:
            self._active.subscribers.discard(client)

    async def _teardown_active(self) -> None:
        if not self._active:
            return

        active = self._active
        self._active = None
        active.halt_task.cancel()
        active.relay_task.cancel()
        for task in (active.halt_task, active.relay_task):
            try:
                await task
            except asyncio.CancelledError:
                pass
        await active.bus.close()

    def _defaults(self) -> dict[str, str]:
        return {
            "repo": settings.spectre_repo,
            "branch": settings.spectre_branch,
            "scope_path": settings.spectre_scope,
        }

    def _load_scopes(self) -> list[ScopeOption]:
        if not self.scope_dir.exists():
            return []
        options: list[ScopeOption] = []
        for path in sorted(self.scope_dir.glob("*.yaml")):
            try:
                scope = RepoScope.load(path)
            except ValueError:
                continue
            options.append(
                ScopeOption(
                    path=str(path),
                    name=scope.name,
                    allowed_repos=scope.allowed_repos,
                    allowed_branches=scope.allowed_branches,
                )
            )
        return options

    def _load_scope(self, scope_path: str) -> RepoScope:
        path = Path(scope_path)
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        else:
            path = path.resolve()

        scope_root = self.scope_dir.resolve()
        try:
            path.relative_to(scope_root)
        except ValueError as exc:
            raise ValueError(f"scope path must be under {scope_root}") from exc
        if not path.exists():
            raise ValueError(f"scope file not found: {scope_path}")
        return RepoScope.load(path)

    async def _send(self, websocket: ServerConnection, payload: dict[str, Any]) -> None:
        await websocket.send(json.dumps(payload))
