# local-research-replay

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [local-arch-orchestrator.md](local-arch-orchestrator.md), [local-tool-websocket-stream.md](local-tool-websocket-stream.md), issue #15

## Summary

Replay a completed engagement from its SQLite event log without re-running agents, GitHub API calls, or scanners. Events are emitted in original order (optionally paced) to stdout and optionally to WebSocket clients.

## Context

Demo playback and debugging need the same UI timeline without new network or tool side effects. Instant “Past session” subscribe remains a catch-up dump; `spectre replay` is the paced demo path.

## Implementation

### CLI

```bash
python -m spectre.cli replay --session eng_<id>
python -m spectre.cli replay --session eng_<id> --speed 1 --ws
```

| Flag | Meaning |
|------|---------|
| `--speed 0` | Immediate (default) |
| `--speed 1` | Real-time inter-event delays |
| `--speed N` | N× faster than recorded deltas |
| `--ws` | Broadcast events on the control WebSocket port |

### Module

`spectre/research/replay.py`

- `load_session_events` — read-only open of `events.db`
- `iter_replay_events` / `replay_session` — ordered playback
- `ReplayWebSocketServer` — fan-out without bus writes

Replay **never** constructs the agent registry, GitHub client, gitleaks, or osv-scanner.

### Safety

- Unknown session → error exit
- Empty event log → error exit
- Negative speed rejected
- No mutation of the session database during replay

## Tests

| Case | Type |
|------|------|
| Sequence fidelity of stored events | Positive |
| Unknown session | Negative |
| Empty session | Negative |
| Negative speed / no tool construction | Negative |

## Changelog

- 2026-06-25 — Initial paced engagement replay (#15)
