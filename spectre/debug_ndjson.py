"""Temporary debug NDJSON logger for session dac8a3."""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from typing import Any

_SESSION = "dac8a3"
_PATHS = (
    Path("/Users/tmestery/Desktop/SPECTRE/.cursor/debug-dac8a3.log"),
    Path("/app/data/sessions/debug-dac8a3.log"),
    Path("data/sessions/debug-dac8a3.log"),
)
_INGEST = "http://host.docker.internal:7900/ingest/6481213c-db08-40e9-8368-29f649f94569"


def dbg(
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict[str, Any] | None = None,
    *,
    run_id: str = "pre-fix",
) -> None:
    # #region agent log
    payload = {
        "sessionId": _SESSION,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data or {},
        "timestamp": int(time.time() * 1000),
    }
    line = json.dumps(payload, default=str) + "\n"
    for path in _PATHS:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError:
            pass
    try:
        req = urllib.request.Request(
            _INGEST,
            data=line.encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Debug-Session-Id": _SESSION,
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=1.5)
    except Exception:
        pass
    # #endregion
