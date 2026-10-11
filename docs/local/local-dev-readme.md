# local-dev-readme

**Status:** active  
**Updated:** 2026-10-10  
**Related:** root [README.md](../../README.md), issue #41

## Summary

The root README is the first-time visitor entry point: branding, scope warning, capability list, Docker/`spectre serve` quickstart, CLI research commands, and doc links.

## Context

After the Phase 4 feature wave (metrics, replay, judges, UI, sample repo), the README needed to stop describing vaporware and match shipped CLI/UI flows.

## Implementation

Keep the README concise:

- Logo under `docs/assets/logo.png`
- Docker Compose + local `serve` / `npm run dev` as primary paths
- CLI: `run`, `report`, `metrics`, `replay`, `halt`
- Link sample repo + judging/UI docs without duplicating `docs/local/`

Planned work stays in [local-plan-roadmap.md](local-plan-roadmap.md), not as unchecked README promises.

## Tests

Manual review against acceptance criteria in #41 (no secrets; accurate quickstart; asset paths).

## Changelog

- 2026-10-10 — README refresh for current capabilities (#41)
