from spectre.server.serve import _HandshakeNoiseFilter, process_request


def test_handshake_noise_filter_suppresses_probe_errors():
    filt = _HandshakeNoiseFilter()
    record = type("LogRecord", (), {"getMessage": lambda self: "opening handshake failed"})()
    assert filt.filter(record) is False


def test_handshake_noise_filter_allows_other_messages():
    filt = _HandshakeNoiseFilter()
    record = type("LogRecord", (), {"getMessage": lambda self: "client connected"})()
    assert filt.filter(record) is True


class _FakeConnection:
    def respond(self, status: int, body: str):
        return (status, body)


class _FakeRequest:
    def __init__(self, path: str, upgrade: str = "") -> None:
        self.path = path
        self.headers = {"Upgrade": upgrade}


def test_process_request_returns_health_for_plain_http():
    response = process_request(_FakeConnection(), _FakeRequest("/health"))
    assert response == (200, "ok\n")


def test_process_request_allows_websocket_upgrade():
    response = process_request(_FakeConnection(), _FakeRequest("/", upgrade="websocket"))
    assert response is None
