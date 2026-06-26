# local-plan-roadmap

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [AGENTS.md](../../AGENTS.md), [local-arch-overview.md](local-arch-overview.md)

## Summary

Master build plan for SPECTRE — a multi-agent **GitHub repository security auditing** system with a visual demo. Phases progress from documentation through a working four-agent crew that audits authorized repos for secrets, vulnerable dependencies, and misconfigurations.

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
- Network pen test against web apps (DVWA optional Phase 4)

## Implementation

### Phase 0 — Foundation (current)

**Goal:** Documentation, schemas, project conventions, empty scaffold.

| Deliverable | Status |
|-------------|--------|
| `AGENTS.md`, `SKILLS.md`, `.cursor/rules/` | Done |
| `docs/local/` architecture and agent docs | In progress (GitHub pivot) |
| `.cursor/skills/` workflow skills | Done |
| `.github/` issue and PR templates | Done |
| Pydantic schemas (`spectre/schemas/`) | Planned |
| Empty `spectre/`, `src/`, `scopes/` layout | Planned |

**Demo milestone:** Docs complete; agent can scaffold from this plan.

### Phase 1 — Bus + Orchestrator + Recon (GitHub)

**Goal:** Event-sourced findings bus, orchestrator loop, Recon agent mapping a repo.

| Deliverable | Notes |
|-------------|-------|
| Findings Bus | SQLite event store + pub/sub |
| Repo scope enforcement | `scopes/*.yaml` allowlist, reject out-of-scope repos |
| GitHub API client | List contents, workflows, languages, clone to temp dir |
| Orchestrator skeleton | Engagement lifecycle, agent registry |
| Recon agent | Publishes `repository`, `file`, `workflow`, `dependency` findings |
| CLI `spectre run --repo` | Start engagement, stream events to stdout |
| WebSocket server | Broadcast bus events for UI (stub OK) |

**Demo milestone:** Recon maps `tmestery/SPECTRE` (or your repo); timeline populates.

**Issue seeds:** `#2` findings bus, `#3` repo scope, `#4` recon agent + GitHub API

### Phase 2 — VulnHunter + Exploiter

**Goal:** Full audit chain through first confirmed finding.

| Deliverable | Notes |
|-------------|-------|
| Handoff protocol v1 | Recon → VulnHunter → Exploiter rules |
| VulnHunter agent | gitleaks, osv-scanner, workflow misconfig checks |
| Exploiter agent | Validate secrets (read-only), confirm CVE reachability |
| Audit log | Every API call and scan recorded |
| Redaction layer | Snippet redaction in bus and UI |

**Demo milestone:** Agents hand off; Exploiter confirms a secret or CVE in target repo.

**Issue seeds:** `#5` handoff protocol, `#6` vuln hunter, `#7` exploiter/validator

### Phase 3 — Reporter + Demo UI

**Goal:** Compelling visual demo — "watch agents audit your repo."

| Deliverable | Notes |
|-------------|-------|
| Reporter agent | Executive summary, findings table, remediation |
| Demo UI (`src/`) | Agent chat, timeline with file links, handoff graph |
| WebSocket integration | Real-time stream from orchestrator |
| Kill switch | UI + CLI halt engagement |
| Report export | Markdown + HTML with GitHub permalinks |

**Demo milestone:** Full recorded demo — recon through report on authorized repo.

**Issue seeds:** `#8` reporter, `#9` demo UI, `#10` websocket, `#11` report export

### Phase 4 — Research instrumentation

**Goal:** Export coordination data for analysis and demo narrative.

| Deliverable | Notes |
|-------------|-------|
| Handoff decision log | Structured JSON per activation |
| Coordination metrics | Time-to-handoff, findings-per-agent, false positive rate |
| Replay mode | Re-run engagement from event log |
| Vulnerable sample repo | Curated test repo with planted findings for repeatable demos |

**Demo milestone:** Export session log; replay audit on sample repo.

**Issue seeds:** `#12` handoff logging, `#13` replay, `#14` sample repo

## Architecture decisions (locked for v1)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Coordination model | Bus + orchestrator | Clear handoff boundaries; easier to log and research |
| Primary target | **GitHub repos** | Real demo on repos you own; concrete findings |
| Primary language | Python orchestration + TS UI | GitHub API + security tool ecosystem |
| LLM integration | Groq default; tool-calling agents | Fast demo inference |
| Event store | SQLite per session | Simple, inspectable |
| UI framework | Vite + React | Matches SanFran3D conventions |

## Open questions (resolve in Phase 1)

1. **LangGraph vs custom loop** — spike in scaffold issue.
2. **Clone vs API-only** — clone needed for gitleaks history; API for metadata. Hybrid likely.
3. **Exploiter boundaries** — validate secrets with read-only checks only; no destructive API calls.

## Tests

N/A — planning doc. Each phase deliverable follows [local-dev-standards.md](local-dev-standards.md).

## Changelog

- 2026-06-25 — Pivot primary target from DVWA to GitHub repos
- 2026-06-25 — Initial roadmap
