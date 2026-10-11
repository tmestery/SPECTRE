import asyncio
import json
from typing import Any

from websockets.asyncio.server import Server, ServerConnection
from websockets.exceptions import ConnectionClosed

from spectre.bus.store import FindingsBus
from spectre.config import settings
from spectre.safety.halt import request_halt
from spectre.schemas.events import EventType
from spectre.server.serve import serve_spectre_ws

RELAYED_EVENTS = [
    EventType.ENGAGEMENT_STARTED,
    EventType.AGENT_ACTIVATED,
    EventType.SUBAGENT_ACTIVATED,
    EventType.AGENT_MESSAGE,
    EventType.FINDING,
    EventType.HANDOFF_DECISION,
    EventType.HANDOFF_VERDICT,
    EventType.TOOL_INVOCATION,
    EventType.LLM_INVOCATION,
    EventType.REPORT_SECTION,
    EventType.REPORT_VERDICT,
    EventType.ENGAGEMENT_HALTED,
    EventType.ENGAGEMENT_COMPLETE,
]


class EngagementWebSocketServer:
    def __init__(self, bus: FindingsBus, session_id: str) -> None:
        self.bus = bus
        self.session_id = session_id
        self._clients: set[ServerConnection] = set()
        self._relay_task: asyncio.Task | None = None
        self._halt_requested = False

    async def start(self) -> Server:
        self._relay_task = asyncio.create_task(self._relay_events())
        return await serve_spectre_ws(self._handler, settings.ws_host, settings.ws_port)

    async def stop(self, server: Server) -> None:
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

    async def _handler(self, websocket: ServerConnection) -> None:
        self._clients.add(websocket)
        try:
            await websocket.send(
                json.dumps(
                    {
                        "type": "subscribed",
                        "session_id": self.session_id,
                        "ws_url": f"ws://localhost:{settings.ws_port}",
                    }
                )
            )
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "halt":
                    self._halt_requested = True
                    request_halt(self.session_id)
                    await websocket.send(json.dumps({"type": "halt_ack", "session_id": self.session_id}))
        finally:
            self._clients.discard(websocket)

    async def _relay_events(self) -> None:
        async for event in self.bus.subscribe(RELAYED_EVENTS):
            payload: dict[str, Any] = event.model_dump(mode="json")
            message = json.dumps(payload)
            dead: list[ServerConnection] = []
            for client in self._clients:
                try:
                    await client.send(message)
                except ConnectionClosed:
                    dead.append(client)
            for client in dead:
                self._clients.discard(client)

    def halt_requested(self) -> bool:
        return self._halt_requested
