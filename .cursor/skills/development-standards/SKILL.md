---
name: development-standards
description: >-
  Enforces SPECTRE development discipline: lab scope only, async/non-blocking I/O,
  minimum test coverage per feature (1 positive + 3 negative), stop-and-fix on any
  breakage, and mandatory docs in docs/local/. Use for every feature, bugfix,
  or refactor in this repo.
---

# Development Standards

Apply these rules on **every** change. They override continuing unrelated work.

## Lab scope (required)

- **Authorized repos only** — every engagement needs `scopes/*.yaml` with `allowed_repos`.
- Tool wrappers **must** call repo scope check before clone or scan.
- Tests **must** include out-of-scope rejection for any tool wrapper or agent action.
- Never commit API keys, real target lists, or session data with captured credentials.

## Async / non-blocking I/O (required)

- Python: `asyncio`, async subprocess for tools, async WebSocket.
- Frontend: async fetch/WebSocket; no blocking UI thread.
- Heavy report generation: background task with progress events.

## Testing (required per feature)

| Type | Minimum | Purpose |
|------|---------|---------|
| Positive | **1** | Happy path — feature works as specified |
| Negative | **3** | Out-of-scope, invalid input, error/edge cases |

- Python: `pytest` in `tests/` or colocated `test_*.py`
- Frontend: Vitest colocated `*.test.ts`
- Mock tool output in tests — never run real nmap/sqlmap in unit tests
- Feature is **not complete** without 1+3

## Stop on breakage (required)

1. **Stop** if tests, types, lint, or build fail.
2. **Fix** root cause.
3. **Re-run** to confirm green.
4. Resume original task.

## Documentation (required)

Document every feature in `docs/local/` before marking work complete. See **document-feature** skill.

## Git workflow (required)

- Issue first → branch → PR to `main`
- See **git-workflow** skill
