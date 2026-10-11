# local-test-strategy

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [local-dev-standards.md](local-dev-standards.md)

## Summary

Testing strategy for SPECTRE — pytest for Python orchestration, Vitest for demo UI, mock tool outputs for agent tests, and optional Docker integration tests for DVWA.

## Context

Offensive tooling cannot run unchecked in CI against real targets. Tests rely on **mocked subprocess output** and **fixture files** representing nmap, nuclei, sqlmap results.

## Implementation

### Test layout

```
tests/
  unit/
    test_scope.py
    test_findings_bus.py
    test_handoffs.py
  agents/
    test_recon.py
    test_vuln_hunter.py
  fixtures/
    nmap_dvwa.xml
    nuclei_sqli.json
    sqlmap_success.log
src/
  **/*.test.ts          # Vitest colocated
```

### 1+3 rule (mandatory)

Every feature:

| # | Type | Example |
|---|------|---------|
| 1 | Positive | Valid input → expected finding |
| 2 | Negative | Out-of-scope rejected |
| 3 | Negative | Malformed tool output handled |
| 4 | Negative | Timeout / empty input / edge case |

### Mock strategy

```python
# tests/conftest.py
@pytest.fixture
def mock_nmap(monkeypatch):
    async def fake_run(*args, **kwargs):
        return Path("tests/fixtures/nmap_dvwa.xml").read_text()
    monkeypatch.setattr("spectre.tools.nmap._run", fake_run)
```

Never run real nmap/sqlmap in unit tests.

### Integration tests (optional CI job)

- `docker compose -f targets/dvwa/docker-compose.yml up -d`
- Run `spectre run --target dvwa --dry-run` (planned flag: validate without LLM)
- Tear down compose

Mark with `@pytest.mark.integration`; skip in default `pytest` run.

### Frontend tests

- Vitest + jsdom
- Mock WebSocket with `vitest` fake timers
- Component tests for FindingCard, SeverityBadge, timeline sort

### CI (active)

Workflow: [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)

Runs on every pull request and push to `main`:

| Job | Commands |
|-----|----------|
| Python | `pip install -e ".[dev]"` → `ruff check spectre/ tests/` → `pytest -q` |
| Mypy | `mypy spectre` — **non-blocking** (`continue-on-error: true`) while typing is gradual |
| UI | `npm ci` → `npm test` → `npm run build` (includes `tsc -b`) |

CI disables live LLM calls (`LLM_ENABLED=false`). No GitHub or Groq secrets are required.

Local mypy: `pip install -e ".[dev]"` then `mypy spectre`. Config lives in `pyproject.toml` under `[tool.mypy]`.

## Tests

N/A — meta doc.

## Changelog

- 2026-06-25 — Added gradual mypy CI job (#36)
- 2026-06-25 — Documented active GitHub Actions CI workflow (#16)
- 2026-06-25 — Initial test strategy
