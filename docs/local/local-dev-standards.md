# local-dev-standards

**Status:** active  
**Updated:** 2026-06-25  
**Related:** `.cursor/skills/development-standards/SKILL.md`, [local-safety-lab-scope.md](local-safety-lab-scope.md)

## Summary

Mandatory development discipline for SPECTRE: lab-only targets, async I/O, minimum test coverage per feature, stop-and-fix on breakage, and documentation for every change.

## Context

SPECTRE runs offensive security tooling. Standards emphasize safety guardrails alongside code quality — out-of-scope rejection is as important as happy-path tests.

## Implementation

### Lab scope (required)

- Every engagement requires a `scope.yaml` with explicit host/IP allowlist.
- Tool wrappers **must** call `safety.scope.check(target)` before execution.
- Tests **must** include out-of-scope rejection for any tool wrapper or agent action.
- Never commit real target lists, credentials, or API keys.

### Async / non-blocking I/O (required)

- Python: `asyncio`, `async` subprocess for tools, async WebSocket.
- Frontend: WebSocket and fetch only; no sync blocking on large JSON parse in render.
- Heavy report generation: background task with progress events.

### Testing (required per feature)

| Type | Minimum | Purpose |
|------|---------|---------|
| Positive | **1** | Happy path — feature works as specified |
| Negative | **3** | Invalid input, out-of-scope, error/edge cases |

- Python: `tests/` or colocated `test_*.py`; run `pytest`.
- Frontend: colocated `*.test.ts`; run `npm test`.
- Feature is **not complete** without 1+3.

**SPECTRE-specific negative tests:**

1. Out-of-scope target rejected
2. Invalid/malformed input handled
3. Timeout or tool failure handled gracefully

### Stop on breakage (required)

1. **Stop** if tests, types, lint, or build fail.
2. **Fix** root cause.
3. **Re-run** to confirm green.
4. Resume original task.

### Documentation (required)

- Every feature: `docs/local/local-<area>-<topic>.md`
- Index in [docs/local/README.md](README.md)
- Use **document-feature** skill template

### Git workflow (required)

- Issue first → branch → PR to `main`
- See [local-dev-git-workflow.md](local-dev-git-workflow.md)

## Tests

N/A — process policy.

## Changelog

- 2026-06-25 — Initial dev standards
