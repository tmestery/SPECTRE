# local-dev-repo-layout

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [local-arch-overview.md](local-arch-overview.md), issue #40

## Summary

Conventions for keeping the SPECTRE repository root readable: branding under `docs/assets/`, generated artifacts gitignored, source packages in `spectre/` and `src/`.

## Context

The root previously held a large `logo.png` next to package manifests and Docker files. Session outputs and build products also clutter a clean checkout if not ignored.

## Implementation

### Branding

| Asset | Path |
|-------|------|
| SPECTRE logo | [`docs/assets/logo.png`](../assets/logo.png) |

README references `./docs/assets/logo.png`. Do not place binary branding assets at the repo root.

### Root expectations

Keep at root only:

- Project docs: `README.md`, `AGENTS.md`, `SKILLS.md`
- Package manifests: `pyproject.toml`, `package.json`, lockfiles
- App entry: `index.html`, Vite/TS configs
- Orchestration: `Dockerfile`, `docker-compose.yml`, `.env.example`
- Source trees: `spectre/`, `src/`, `tests/`, `scopes/`, `docs/`, `.github/`, `.cursor/`

### Generated / local (gitignored)

| Path | Role |
|------|------|
| `dist/` | Vite production build |
| `reports/*` | Exported audit reports (`.gitkeep` retained) |
| `data/sessions/*` | Engagement event DBs (`.gitkeep` retained) |
| `*.tsbuildinfo` | TypeScript incremental build cache |
| `.venv/`, `node_modules/` | Local environments |

## Tests

N/A — layout convention.

## Changelog

- 2026-06-25 — Moved logo to `docs/assets/`; documented root hygiene (#40)
