# local-plan-roadmap

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [AGENTS.md](../../AGENTS.md), [local-arch-overview.md](local-arch-overview.md)

## Summary

Master build plan for SPECTRE — a multi-agent penetration testing system with a visual demo. Phases progress from documentation and schemas through a working four-agent crew against DVWA, ending with handoff research instrumentation.

## Context

### Vision

Watch a crew of specialized AI agents collaboratively pen test an authorized lab target. The demo is visual and compelling: agents talk to each other, findings accumulate on a timeline, and you see progressive compromise of a deliberately vulnerable system (DVWA first, HackTheBox-style later).

### Research angle

How do agents **coordinate**, **share findings**, and **decide what to hand off**? SPECTRE treats the handoff protocol as a first-class design artifact — every activation is logged with inputs, rules fired, and human-readable rationale.

### Non-goals (v1)

- Real-world target scanning or exploitation
- Cloud deployment or SaaS multi-tenancy
- Full HackTheBox API integration
- Autonomous post-exploitation / lateral movement
- C2 frameworks or persistence mechanisms

## Implementation

### Phase 0 — Foundation (current)

**Goal:** Documentation, schemas, project conventions, empty scaffold.

| Deliverable | Status |
|-------------|--------|
| `AGENTS.md`, `SKILLS.md`, `.cursor/rules/` | Done |
| `docs/local/` architecture and agent docs | Done |
| `.cursor/skills/` workflow skills | Done |
| `.github/` issue and PR templates | Done |
| Pydantic schemas (`spectre/schemas/`) | Planned |
| Empty `spectre/`, `src/`, `targets/` layout | Planned |

**Demo milestone:** Docs complete; agent can scaffold from this plan.

### Phase 1 — Bus + Orchestrator + Recon

**Goal:** Event-sourced findings bus, orchestrator loop, Recon agent against DVWA.

| Deliverable | Notes |
|-------------|-------|
| Findings Bus | SQLite or in-memory event store + pub/sub |
| Scope enforcement | `scope.yaml` allowlist, reject out-of-scope |
| Orchestrator skeleton | Engagement lifecycle, agent registry |
| Recon agent | nmap + httpx wrappers, publishes `host`, `open_port`, `service` |
| CLI `spectre run` | Start engagement, stream events to stdout |
| WebSocket server | Broadcast bus events for UI (stub OK) |

**Demo milestone:** Recon discovers DVWA ports/services; timeline populates in terminal or minimal UI.

**Issue seeds:** `#1` scaffold, `#2` findings bus, `#3` scope enforcement, `#4` recon agent

### Phase 2 — VulnHunter + Exploiter + DVWA

**Goal:** Full attack chain through first confirmed exploit.

| Deliverable | Notes |
|-------------|-------|
| Handoff protocol v1 | Recon → VulnHunter → Exploiter rules |
| VulnHunter agent | nuclei templates, SQLi/XSS probes for DVWA |
| Exploiter agent | sqlmap wrapper, curl PoC scripts |
| DVWA target | `targets/dvwa/docker-compose.yml` + `scope.yaml` |
| Audit log | Every tool call recorded |

**Demo milestone:** Agents hand off; Exploiter confirms SQLi or similar DVWA vuln.

**Issue seeds:** `#5` handoff protocol, `#6` vuln hunter, `#7` exploiter, `#8` dvwa target

### Phase 3 — Reporter + Demo UI

**Goal:** Compelling visual demo — the "watch agents break in" experience.

| Deliverable | Notes |
|-------------|-------|
| Reporter agent | Executive summary, findings table, remediation |
| Demo UI (`src/`) | Agent chat, findings timeline, handoff graph |
| WebSocket integration | Real-time stream from orchestrator |
| Kill switch | UI + CLI halt engagement |
| Report export | Markdown + HTML artifacts |

**Demo milestone:** Full recorded demo — recon through report on DVWA with live UI.

**Issue seeds:** `#9` reporter, `#10` demo UI shell, `#11` websocket stream, `#12` report export

### Phase 4 — Research instrumentation

**Goal:** Export coordination data for analysis and paper/demo narrative.

| Deliverable | Notes |
|-------------|-------|
| Handoff decision log | Structured JSON per activation |
| Coordination metrics | Time-to-handoff, findings-per-agent, false positive rate |
| Replay mode | Re-run engagement from event log |
| A/B handoff rules | Toggle threshold configs for comparison |

**Demo milestone:** Export session log; compare two handoff strategies side by side.

**Issue seeds:** `#13` handoff logging, `#14` replay mode, `#15` metrics export

## Architecture decisions (locked for v1)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Coordination model | Bus + orchestrator (not direct agent chat) | Clear handoff boundaries; easier to log and research |
| Primary language | Python orchestration + TS UI | Ecosystem for security tools + strong demo frontend |
| LLM integration | Tool-calling agents with structured output | Agents reason; tools produce evidence |
| Event store | SQLite (file per session) | Simple, inspectable, no external deps for demo |
| Target v1 | DVWA in Docker | Well-known vulns, fast setup, compelling demo path |
| UI framework | Vite + React | Matches SanFran3D conventions; fast iteration |

## Open questions (resolve in Phase 1)

1. **LangGraph vs custom loop** — LangGraph gives graph visualization; custom loop is simpler. Spike in `#1` scaffold issue.
2. **LLM provider** — Groq (default), OpenAI, Anthropic, or Ollama. Config via `.env`; never commit keys.
3. **Agent message format** — Full reasoning vs summary-only for demo UI. Default: summary + evidence links.

## Tests

N/A — planning doc. Each phase deliverable follows [local-dev-standards.md](local-dev-standards.md) (1 positive + 3 negative per feature).

## Changelog

- 2026-06-25 — Initial roadmap
