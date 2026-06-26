import logging
from collections.abc import Awaitable, Callable

import websockets
from websockets.server import ServerConnection

logger = logging.getLogger(__name__)


class _HandshakeNoiseFilter(logging.Filter):
    """Drop stack traces for port probes that open TCP then close without a request."""

    _NOISE = (
        "opening handshake failed",
        "did not receive a valid HTTP request",
        "connection closed while reading HTTP request line",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(fragment in message for fragment in self._NOISE)


def _configure_ws_logging() -> None:
    ws_logger = logging.getLogger("websockets.server")
    if not any(isinstance(f, _HandshakeNoiseFilter) for f in ws_logger.filters):
        ws_logger.addFilter(_HandshakeNoiseFilter())


def process_request(connection: ServerConnection, request) -> websockets.Response | None:
    if request.headers.get("Upgrade", "").lower() == "websocket":
        return None
    body = "SPECTRE WebSocket control server — connect with WebSocket upgrade.\n"
    if request.path == "/health":
        body = "ok\n"
    return connection.respond(200, body)


async def serve_spectre_ws(
    handler: Callable[[ServerConnection], Awaitable[None]],
    host: str,
    port: int,
) -> websockets.Server:
    _configure_ws_logging()
    return await websockets.serve(
        handler,
        host,
        port,
        process_request=process_request,
        ping_interval=20,
        ping_timeout=20,
    )
