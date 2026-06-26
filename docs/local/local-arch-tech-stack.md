# local-arch-tech-stack

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [local-plan-roadmap.md](local-plan-roadmap.md), [local-arch-overview.md](local-arch-overview.md)

## Summary

Technology choices for SPECTRE v1 — Python orchestration, React demo UI, Docker lab targets, SQLite event store, and LLM tool-calling agents.

## Context

Stack prioritizes: (1) security tool ecosystem, (2) real-time demo UX, (3) inspectable coordination logs, (4) minimal external dependencies for local demo.

## Implementation

### Stack overview

| Layer | Technology | Notes |
|-------|------------|-------|
| Orchestration | Python 3.12+ | asyncio, Pydantic v2 |
| Agent framework | LangGraph *or* custom loop | Spike in Phase 1; see open question |
| LLM | Configurable (Groq / OpenAI / Anthropic / Ollama) | Via `.env`; structured tool output. **Groq recommended for demo** (fast, OpenAI-compatible) |
| Event store | SQLite | Per-session at `data/sessions/<id>/` |
| WebSocket | `websockets` or FastAPI | Stream bus events to UI |
| REST API | FastAPI (optional v1) | Finding detail, report download |
| Demo UI | Vite + React 18 + TypeScript | Match SanFran3D conventions |
| UI state | React context + WebSocket hook | No Redux unless needed |
| Styling | CSS modules or Tailwind | TBD at UI scaffold |
| Lab targets | Docker Compose | DVWA v1 |
| Python tests | pytest + pytest-asyncio | `tests/` |
| Frontend tests | Vitest | Colocated `*.test.ts` |
| Linting | ruff (Python), ESLint (TS) | |
| Type checking | mypy (Python), tsc strict (TS) | |

### Security tools (wrapped, not embedded)

| Tool | Agent | Install |
|------|-------|---------|
| nmap | Recon | System package or Docker sidecar |
| httpx | Recon | Go binary or pip wrapper |
| nuclei | VulnHunter | Binary + templates |
| nikto | VulnHunter | Perl script |
| sqlmap | Exploiter | pip / git |
| curl | Exploiter | System |

Tools run as **async subprocess** with timeout, scope check, and output capture. Never shell-interpolate user input.

### LLM integration pattern

```python
# Agent calls LLM with tool definitions; LLM returns structured tool calls
response = await llm.chat(
    system=load_prompt("recon/prompt.md"),
    messages=ctx.prior_messages,
    tools=[nmap_tool.schema(), httpx_tool.schema()],
)
# Execute tool calls via sandboxed wrappers
# Parse results → Finding objects
# Publish to bus
```

**Structured output:** Use JSON mode or tool-calling; validate with Pydantic before bus publish.

### Project files (planned)

```
pyproject.toml          # Python deps, spectre package
package.json            # UI deps
docker-compose.yml      # Optional: dev orchestrator + DVWA
.env.example            # LLM_API_KEY, WS_PORT, etc.
```

### Dependencies (initial)

**Python:**
- `pydantic>=2`
- `pytest`, `pytest-asyncio`
- `websockets` or `fastapi` + `uvicorn`
- `langgraph` (if chosen) or none for custom loop

**Node:**
- `vite`, `react`, `typescript`
- `vitest`

### Open decisions (Phase 1 spike)

| Question | Options | Decide by |
|----------|---------|-----------|
| Agent framework | LangGraph vs custom asyncio loop | Issue #1 |
| API layer | FastAPI combined vs standalone WS | Issue #1 |
| Tool isolation | Host binaries vs tool Docker sidecar | Issue #8 (DVWA) |

## Tests

N/A — reference doc. Tool wrapper tests in Phase 1–2.

## Changelog

- 2026-06-25 — Initial tech stack doc
