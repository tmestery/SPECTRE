# local-plan-roadmap

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [AGENTS.md](../../AGENTS.md), [local-arch-overview.md](local-arch-overview.md)

## Summary

Master build plan for SPECTRE — a multi-agent **GitHub repository security auditing** system with a visual demo. Phases 0–3 are complete; Phase 4 research instrumentation and judging work continues.

## Context

### Vision

Watch a crew of specialized AI agents collaboratively audit a GitHub repository. The demo is visual and compelling: agents talk to each other, findings accumulate on a timeline with file links, and you see progressive discovery of real issues (leaked secrets, CVEs, unsafe workflows) in a repo you own.

### Research angle

How do agents **coordinate**, **share findings**, and **decide what to hand off**? SPECTRE treats the handoff protocol as a first-class design artifact — every activation is logged with inputs, rules fired, and human-readable rationale.

### Non-goals (v1)

- Scanning arbitrary public repos without authorization
- Mass org-wide or GitHub search sweeps
- Auto-opening PRs or committing fixes without human approval
- Cloud deployment or SaaS multi-tenancy
- Network pen test against web apps (DVWA optional / deprecated for v1)

## Implementation

### Phase 0 — Foundation (complete)

**Goal:** Documentation, schemas, project conventions, scaffold.

| Deliverable | Status |
|-------------|--------|
| `AGENTS.md`, `SKILLS.md`, `.cursor/rules/` | Done |
| `docs/local/` architecture and agent docs | Done |
| `.cursor/skills/` workflow skills | Done |
| `.github/` issue and PR templates | Done — see [local-dev-github-templates.md](local-dev-github-templates.md) (#51) |
| Pydantic schemas (`spectre/schemas/`) | Done |
| `spectre/`, `src/`, `scopes/` layout | Done |

**Demo milestone:** Docs complete; agent can scaffold from this plan.

### Phase 1 — Bus + Orchestrator + Recon (complete)

**Goal:** Event-sourced findings bus, orchestrator loop, Recon agent mapping a repo.

| Deliverable | Status |
|-------------|--------|
| Findings Bus | Done — SQLite event store + pub/sub |
| Repo scope enforcement | Done — `scopes/*.yaml` allowlist |
| GitHub API client | Done |
| Orchestrator skeleton | Done |
| Recon agent | Done |
| CLI `spectre run --repo` | Done |
| WebSocket / control server | Done — `spectre serve` |

**Demo milestone:** Recon maps an authorized repo; timeline populates.

**Issues:** #2–#7 (closed)

### Phase 2 — VulnHunter + Exploiter (complete)

**Goal:** Full audit chain through first confirmed finding.

| Deliverable | Status |
|-------------|--------|
| Handoff protocol v1 | Done |
| VulnHunter agent | Done — gitleaks fallback, osv-scanner, workflow analyzer |
| Exploiter agent | Done — format/reachability/workflow validation |
| Audit log | Done |
| Redaction layer | Done |

**Demo milestone:** Agents hand off; Exploiter confirms secrets or workflow misconfigs.

**Issues:** #8, #9 (closed)

### Phase 3 — Reporter + Demo UI (complete)

**Goal:** Compelling visual demo — "watch agents audit your repo."

| Deliverable | Status |
|-------------|--------|
| Reporter agent | Done — markdown/HTML export, GitHub permalinks |
| Demo UI (`src/`) | Done — functional; visual redesign tracked in #28 |
| WebSocket integration | Done |
| Kill switch | Done — UI + CLI |
| Report export | Done — `spectre report --session <id>` |
| LLM + reasoning loop | Done — Groq subagents + `AgentReasoningLoop` |

**Demo milestone:** Full recorded demo — recon through report on authorized repo.

**Issues:** #10, #11, #12 (closed)

### Phase 4 — Research instrumentation (in progress)

**Goal:** Export coordination data for analysis, demo narrative, and judging layer.

| Deliverable | Status | Issue |
|-------------|--------|-------|
| Coordination metrics + handoff JSONL | Done — `spectre metrics` | [#14](https://github.com/tmestery/SPECTRE/issues/14) |
| Engagement replay | Done — `spectre replay` | [#15](https://github.com/tmestery/SPECTRE/issues/15) |
| CI pipeline | Done | [#16](https://github.com/tmestery/SPECTRE/issues/16) |
| Judging agent ADR | Done (design) | [#22](https://github.com/tmestery/SPECTRE/issues/22) |
| Vulnerable sample repo | Open | [#13](https://github.com/tmestery/SPECTRE/issues/13) |
| Demo UI redesign | Open | [#28](https://github.com/tmestery/SPECTRE/issues/28) |
| Judging schemas + agents | Open | [#29](https://github.com/tmestery/SPECTRE/issues/29)–[#34](https://github.com/tmestery/SPECTRE/issues/34) |
| README refresh | Open (end of wave) | [#41](https://github.com/tmestery/SPECTRE/issues/41) |

**Demo milestone:** Export session metrics; replay audit; optional sample-repo demo.

## Architecture decisions (locked for v1)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Coordination model | Bus + orchestrator | Clear handoff boundaries; easier to log and research |
| Primary target | **GitHub repos** | Real demo on repos you own; concrete findings |
| Primary language | Python orchestration + TS UI | GitHub API + security tool ecosystem |
| LLM integration | Groq default; tool-calling agents | Fast demo inference |
| Event store | SQLite per session | Simple, inspectable |
| UI framework | Vite + React | Fast local demo UI |
| Judging (v1) | Advisory only | Bus-first verdicts; do not block handoffs |

## Open questions

1. **Judging blocking mode (v2)** — when to pause handoffs on `reject` (critical-only?).
2. **Sample repo hosting** — dedicated planted-findings repo vs fixtures in this monorepo (#13).
3. **Exploiter boundaries** — keep validation read-only; no destructive API calls.

## Tests

N/A — planning doc. Each phase deliverable follows [local-dev-standards.md](local-dev-standards.md).

## Changelog

- 2026-06-25 — Synced Phase 0–4 status and issue numbers (#35)
- 2026-06-26 — Phase 3 complete (Reporter + Demo UI + WebSocket)
- 2026-06-25 — Pivot primary target from DVWA to GitHub repos
- 2026-06-25 — Initial roadmap
