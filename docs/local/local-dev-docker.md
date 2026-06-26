# local-dev-docker

**Status:** active
**Updated:** 2026-06-25
**Related:** `Dockerfile`, `docker-compose.yml`, `spectre/server/control.py`, `spectre/cli.py serve`

## Summary

Run the SPECTRE demo stack — control server, WebSocket stream, and dashboard UI — with a single `docker compose up`. Start audits from the UI; no CLI session handoff required.

## Context

Docker Compose bundles nginx (static UI), a long-running WebSocket control server (`spectre serve`), and scanning tools (`gitleaks`, `osv-scanner`, `git`). The UI connects on load and sends `start_engagement` over WebSocket.

## Implementation

| Path | Role |
|------|------|
| `Dockerfile` | Multi-stage build: UI + `runtime` demo image + slim `cli` image |
| `docker-compose.yml` | `spectre` demo service; optional `cli` profile for report/halt/sessions |
| `docker/entrypoint.sh` | nginx on 8080 + `spectre serve` |
| `spectre/server/control.py` | WebSocket control plane: start, subscribe, halt, list sessions |
| `spectre/cli.py serve` | Long-running control server for UI and Docker |

### Ports

| Port | Service |
|------|---------|
| 8080 | Demo dashboard (nginx) |
| 8765 | WebSocket control + event stream |

### UI flow

1. Open http://localhost:8080
2. UI auto-connects to `ws://localhost:8765`
3. Server sends `server_hello` with scope defaults and past sessions
4. Click **Start audit** — no CLI step required
5. Use **Past session** dropdown to replay completed runs

### Quick start

```bash
cp .env.example .env
# Set GITHUB_TOKEN in .env

docker compose up --build
```

### CLI helpers

```bash
docker compose --profile cli run --rm cli sessions
docker compose --profile cli run --rm cli report --session eng_abc123
docker compose --profile cli run --rm cli halt --session eng_abc123
```

Use a real `session_id` from the UI or `sessions` output — `eng_abc123` is only an example.

### Local development (without Docker)

```bash
# Terminal 1
python -m spectre.cli serve

# Terminal 2
npm run dev
```

Open http://localhost:5173 and click **Start audit**.

## Tests

- `tests/test_control_server.py` — start validation, subscribe replay, halt guard
- `tests/test_sessions.py` — session listing
- `tests/test_docker.py` — compose + container config

## Changelog

- **2026-06-25** — UI-driven starts via `spectre serve`; Docker no longer auto-runs engagements.
- **2026-06-25** — Initial Docker Compose stack.
