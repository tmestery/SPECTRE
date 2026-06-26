# local-dev-docker

**Status:** active
**Updated:** 2026-06-25
**Related:** `Dockerfile`, `docker-compose.yml`, `docker/entrypoint.sh`, issue docker-compose

## Summary

Run the full SPECTRE demo stack — orchestrator, WebSocket stream, and dashboard UI — with a single `docker compose up` command. Scanning tools (`gitleaks`, `osv-scanner`, `git`) are baked into the image.

## Context

Local development previously required two terminals: one for `python -m spectre.cli run --ws` and one for `npm run dev`. Docker Compose bundles nginx (static UI), the Python crew, and tool binaries so demos are repeatable without local Node/Python installs.

## Implementation

| Path | Role |
|------|------|
| `Dockerfile` | Multi-stage build: Vite UI → static assets; Python 3.12 runtime + scanners |
| `docker-compose.yml` | `spectre` demo service; optional `cli` profile for report/halt |
| `docker/entrypoint.sh` | Starts nginx on port 8080, then runs engagement with `--ws` |
| `docker/nginx.conf` | Serves built UI with SPA fallback |
| `spectre/config.py` | `WS_HOST` (default `127.0.0.1`; set `0.0.0.0` in containers) |

### Ports

| Port | Service |
|------|---------|
| 8080 | Demo dashboard (nginx) |
| 8765 | WebSocket event stream |

### Environment

Copy `.env.example` to `.env` and set at minimum `GITHUB_TOKEN`. Optional overrides:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SPECTRE_REPO` | `tmestery/SPECTRE` | Target `owner/repo` |
| `SPECTRE_SCOPE` | `scopes/spectre.yaml` | Scope file path inside container |
| `SPECTRE_BRANCH` | `main` | Branch to audit |
| `SPECTRE_UI_DELAY` | `3` | Seconds before engagement starts |
| `VITE_WS_URL` | `ws://localhost:8765` | Baked into UI at image build time |

### Quick start

```bash
cp .env.example .env
# Set GITHUB_TOKEN (e.g. export GITHUB_TOKEN="$(gh auth token)" in .env)

docker compose up --build
```

Open http://localhost:8080. When the first JSON line prints in the logs with `session_id`, connect in the UI or visit `http://localhost:8080/?session=<session_id>`.

### CLI without full demo

```bash
docker compose --profile cli run --rm cli report --session eng_abc123
docker compose --profile cli run --rm cli halt --session eng_abc123
```

Volumes persist session data under `./data/sessions` and reports under `./reports`.

## Tests

`tests/test_docker.py` — compose file shape, `WS_HOST` settings, Dockerfile tool declarations, entrypoint permissions.

## Changelog

- **2026-06-25** — Initial Docker Compose stack for one-command demo runs.
