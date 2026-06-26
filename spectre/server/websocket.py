import asyncio
import json
from typing import Any

import websockets
from websockets.server import WebSocketServerProtocol

from spectre.bus.store import FindingsBus
from spectre.config import settings
from spectre.schemas.events import EventType


class EngagementWebSocketServer:
    def __init__(self, bus: FindingsBus, session_id: str) -> None:
        self.bus = bus
        self.session_id = session_id
        self._clients: set[WebSocketServerProtocol] = set()
        self._relay_task: asyncio.Task | None = None
        self._halt_callback: asyncio.Event = asyncio.Event()

    async def start(self) -> asyncio.Server:
        self._relay_task = asyncio.create_task(self._relay_events())
        return await websockets.serve(self._handler, "localhost", settings.ws_port)

    async def stop(self, server: asyncio.Server) -> None:
        server.close()
        await server.wait_closed()
        if self._relay_task:
            self._relay_task.cancel()
            try:
                await self._relay_task
            except asyncio.CancelledError:
                pass
        for client in list(self._clients):
            await client.close()

    async def _handler(self, websocket: WebSocketServerProtocol) -> None:
        self._clients.add(websocket)
        try:
            await websocket.send(json.dumps({"type": "subscribed", "session_id": self.session_id}))
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "halt":
                    self._halt_callback.set()
                    await websocket.send(json.dumps({"type": "halt_ack"}))
        finally:
            self._clients.discard(websocket)

    async def _relay_events(self) -> None:
        async for event in self.bus.subscribe(
            [
                EventType.AGENT_MESSAGE,
                EventType.FINDING,
                EventType.HANDOFF_DECISION,
                EventType.ENGAGEMENT_COMPLETE,
            ]
        ):
            payload: dict[str, Any] = event.model_dump(mode="json")
            message = json.dumps(payload)
            dead: list[WebSocketServerProtocol] = []
            for client in self._clients:
                try:
                    await client.send(message)
                except websockets.ConnectionClosed:
                    dead.append(client)
            for client in dead:
                self._clients.discard(client)

    def halt_requested(self) -> bool:
        return self._halt_callback.is_set()

    def clear_halt(self) -> None:
        self._halt_callback.clear()
