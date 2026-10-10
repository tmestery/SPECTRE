# local-tool-websocket-stream

**Status:** active  
**Updated:** 2026-06-26  
**Related:** [local-ui-demo-dashboard.md](local-ui-demo-dashboard.md), [local-arch-orchestrator.md](local-arch-orchestrator.md)

## Summary

WebSocket server relays Findings Bus events to the demo UI in real time. Clients connect to `ws://localhost:8765` when the orchestrator runs with `--ws`.

## Implementation

### Relayed event types

`engagement_started`, `agent_activated`, `agent_message`, `finding`, `handoff_decision`, `tool_invocation`, `report_section`, `engagement_halted`, `engagement_complete`

### Halt protocol

Client sends:

```json
{ "type": "halt", "session_id": "eng_…" }
```

Server acknowledges with `halt_ack` and writes `data/sessions/<id>/halt.signal` for cross-process halt.

### CLI

```bash
python -m spectre.cli run --repo owner/repo --scope scopes/x.yaml --ws
python -m spectre.cli halt --session eng_…
python -m spectre.cli replay --session eng_… --speed 1 --ws
```

Replay uses `ReplayWebSocketServer` (read-only fan-out). Instant past-session load via control `subscribe` remains a catch-up dump; paced demo playback is `spectre replay`.

## Tests

| Case | Type |
|------|------|
| Halt signal file created/cleared | Positive |
| Missing halt signal returns false | Negative |

## Changelog

- 2026-06-25 — Documented replay WebSocket path (#15)
- 2026-06-26 — Phase 3 WebSocket + halt signal file
