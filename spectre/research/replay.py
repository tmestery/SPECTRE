"""Paced engagement replay from the session event store (no agents or tools)."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Callable, Coroutine
from pathlib import Path
from typing import Any

from websockets.asyncio.server import Server, ServerConnection
from websockets.exceptions import ConnectionClosed

from spectre.bus.store import FindingsBus
from spectre.config import settings
from spectre.schemas.events import BusEvent
from spectre.server.serve import serve_spectre_ws

logger = logging.getLogger(__name__)

EventHandler = Callable[[BusEvent], Coroutine[Any, Any, None] | None]


async def load_session_events(data_dir: Path, session_id: str) -> list[BusEvent]:
    """Load ordered events for a session. Raises FileNotFoundError / ValueError."""
    db_path = data_dir / session_id / "events.db"
    if not db_path.exists():
        raise FileNotFoundError(f"session not found: {session_id}")

    bus = FindingsBus(db_path)
    await bus.connect()
    try:
        events = await bus.all_events()
    finally:
        await bus.close()

    if not events:
        raise ValueError(f"no events for session: {session_id}")
    return events


async def iter_replay_events(
    events: list[BusEvent],
    *,
    speed: float = 0.0,
) -> AsyncIterator[BusEvent]:
    """Yield events in sequence_num order with optional pacing.

    ``speed=0`` (default) emits immediately.
    ``speed=1`` waits according to original inter-event deltas.
    ``speed>1`` accelerates; ``0 < speed < 1`` slows down.
    """
    if speed < 0:
        raise ValueError("speed must be >= 0")

    prev_ts = None
    for event in events:
        if speed > 0 and prev_ts is not None:
            delta = (event.timestamp - prev_ts).total_seconds()
            if delta > 0:
                await asyncio.sleep(delta / speed)
        prev_ts = event.timestamp
        yield event


async def replay_session(
    data_dir: Path,
    session_id: str,
    *,
    speed: float = 0.0,
    on_event: EventHandler | None = None,
) -> list[BusEvent]:
    """Replay a session's event log without agents, scanners, or GitHub calls."""
    events = await load_session_events(data_dir, session_id)
    emitted: list[BusEvent] = []
    async for event in iter_replay_events(events, speed=speed):
        emitted.append(event)
        if on_event is not None:
            result = on_event(event)
            if asyncio.iscoroutine(result):
                await result
    return emitted


class ReplayWebSocketServer:
    """Broadcast replayed events to WebSocket clients (read-only; no bus writes)."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self._clients: set[ServerConnection] = set()

    async def start(self) -> Server:
        return await serve_spectre_ws(self._handler, settings.ws_host, settings.ws_port)

    async def stop(self, server: Server) -> None:
        server.close()
        await server.wait_closed()
        for client in list(self._clients):
            await client.close()
        self._clients.clear()

    async def broadcast(self, event: BusEvent) -> None:
        message = json.dumps(event.model_dump(mode="json"))
        dead: list[ServerConnection] = []
        for client in self._clients:
            try:
                await client.send(message)
            except ConnectionClosed:
                dead.append(client)
        for client in dead:
            self._clients.discard(client)

    async def _handler(self, websocket: ServerConnection) -> None:
        self._clients.add(websocket)
        try:
            await websocket.send(
                json.dumps(
                    {
                        "type": "subscribed",
                        "session_id": self.session_id,
                        "mode": "replay",
                        "ws_url": f"ws://{settings.ws_host}:{settings.ws_port}",
                    }
                )
            )
            async for _message in websocket:
                pass
        finally:
            self._clients.discard(websocket)
