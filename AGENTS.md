# SPECTRE — Agent Guide

## Project summary

SPECTRE is a **multi-agent penetration testing system** where a crew of specialized AI agents collaboratively assess **authorized lab targets** (DVWA, HackTheBox-style VMs, local Docker ranges). One agent performs reconnaissance, one hunts vulnerabilities, one attempts exploits, and one writes the report. The research angle is **how agents coordinate, share findings, and decide what to hand off** — visible in a compelling demo UI where you watch agents talk to each other and progressively break into a deliberately vulnerable target.

**SPECTRE** = **S**elf-coordinating **P**enetration and **E**xploit **C**rew for **T**hreat **R**esearch and **E**xposure.

## Target architecture

Greenfield repo. Follow this layout when scaffolding:

```
spectre/                    # Python orchestration core
  agents/                   # Recon, VulnHunter, Exploiter, Reporter
  orchestrator/             # Crew loop, handoffs, scheduling
  bus/                      # Shared findings store + event pub/sub
  tools/                    # Sandboxed wrappers (nmap, nuclei, sqlmap, curl)
  schemas/                  # Finding, Handoff, Engagement, Report models
  safety/                   # Scope enforcement, allowlists, audit log
  cli.py                    # `spectre run`, `spectre report`
src/                        # Vite + React demo UI
  app/                      # Shell, providers, layout
  crew/                     # Agent chat stream, handoff timeline
  findings/                 # Finding cards, severity filters
  target/                   # Target status, scope banner
  report/                   # Live report preview
targets/                    # Docker Compose lab targets (DVWA v1)
  dvwa/
docs/local/                 # Local documentation (local-<area>-<topic>.md)
tests/                      # Python unit + integration tests
```

## Core systems

### Agent crew

Four specialized agents with distinct roles and tool access:

| Agent | Role | Tools (v1) | Hands off to |
|-------|------|------------|--------------|
| **Recon** | Discovery — hosts, ports, services, tech stack | nmap, httpx, whatweb, dir enum | VulnHunter |
| **VulnHunter** | Vulnerability identification — misconfigs, CVEs, weak auth | nuclei, nikto, manual probes | Exploiter |
| **Exploiter** | Proof-of-concept exploitation — confirm impact | sqlmap, curl, custom PoC scripts | Reporter |
| **Reporter** | Synthesis — executive summary, findings table, remediation | read-only bus access | (terminal) |

Agents do **not** call each other directly. All coordination flows through the **Findings Bus** and **Orchestrator**.

### Findings Bus (shared memory)

Central event-sourced store where agents publish structured findings and subscribe to relevant updates.

```json
{
  "id": "fnd_8k2m",
  "type": "open_port",
  "agent": "recon",
  "target": "http://dvwa.local",
  "severity": "info",
  "confidence": 0.95,
  "title": "HTTP on port 80",
  "evidence": { "port": 80, "service": "apache", "banner": "Apache/2.4.41" },
  "handoff_hint": "vuln_hunter",
  "status": "confirmed",
  "created_at": "2026-06-25T12:00:00Z"
}
```

Finding types: `host`, `open_port`, `service`, `vulnerability`, `exploit_attempt`, `credential`, `note`.

See [docs/local/local-arch-findings-bus.md](docs/local/local-arch-findings-bus.md).

### Handoff protocol

The orchestrator evaluates findings and triggers agent activation:

1. **Recon** publishes discovery findings → orchestrator queues **VulnHunter** when `open_port` or `service` findings exist for in-scope hosts.
2. **VulnHunter** publishes `vulnerability` findings with `exploitability` score → orchestrator queues **Exploiter** when score ≥ threshold.
3. **Exploiter** publishes `exploit_attempt` with `status: success` → orchestrator queues **Reporter** for synthesis.
4. **Reporter** reads full bus state and emits structured report artifacts.

Handoff decisions are logged for the demo UI and research analysis. See [docs/local/local-arch-handoff-protocol.md](docs/local/local-arch-handoff-protocol.md).

### Safety & scope (mandatory)

- **Lab targets only** — engagements require an explicit scope file with allowed hosts/IPs.
- **Allowlist enforcement** — tools refuse to run against out-of-scope targets; orchestrator aborts on violation.
- **No real-world targets** without explicit written authorization in scope config.
- **Audit log** — every tool invocation, finding, and handoff is recorded.
- **Human kill switch** — demo UI and CLI support immediate engagement halt.

See [docs/local/local-safety-lab-scope.md](docs/local/local-safety-lab-scope.md).

### Demo UI

Real-time visualization of the crew at work:

- **Agent chat panel** — inter-agent messages and reasoning summaries (not raw chain-of-thought).
- **Findings timeline** — chronological bus events with severity badges.
- **Handoff graph** — who triggered whom and why.
- **Target status** — scope banner, connection health, compromise indicators.
- **Live report** — Reporter output streams in as findings accumulate.

See [docs/local/local-ui-demo-dashboard.md](docs/local/local-ui-demo-dashboard.md).

### Lab targets (v1)

| Target | Purpose | Compose path |
|--------|---------|--------------|
| **DVWA** | Primary demo — SQLi, XSS, CSRF, file upload | `targets/dvwa/docker-compose.yml` |
| **Juice Shop** | Phase 2 — modern OWASP top 10 | `targets/juice-shop/` (planned) |
| **HTB-style VM** | Phase 3 — full-box engagement | documented, not automated v1 |

See [docs/local/local-target-dvwa.md](docs/local/local-target-dvwa.md).

## Development standards (mandatory)

Apply on every change. See [docs/local/local-dev-standards.md](docs/local/local-dev-standards.md) and `.cursor/skills/development-standards/`.

- **Authorized targets only** — never run offensive tools against non-lab hosts.
- **Async I/O only** — non-blocking tool execution, WebSocket streaming, async Python (`asyncio`).
- **Tests per feature** — minimum **1 positive** and **3 negative** tests for each new feature.
- **Stop on breakage** — if tests, types, lint, or build fail, stop immediately, fix, verify green, then resume.
- **Document everything** — every feature gets a doc in `docs/local/local-<area>-<topic>.md`. Index in [docs/local/README.md](docs/local/README.md).
- **Issues and PRs** — every change starts with a GitHub issue, ships via a PR to `main` (never commit directly to `main`). See [docs/local/local-dev-git-workflow.md](docs/local/local-dev-git-workflow.md) and **git-workflow** skill.

## Project skills

Use skills in `.cursor/skills/` for workflows:

| Skill | When to use |
|-------|-------------|
| `development-standards` | Every feature, bugfix, refactor |
| `document-feature` | Writing or updating `docs/local/` docs |
| `git-workflow` | Issues, branches, commits, PRs — before any git change |
| `add-agent` | New agent role or extending an existing agent |
| `add-tool-wrapper` | Wrapping a new offensive/security tool |
| `run-engagement` | Running a full pen test engagement against a lab target |
| `setup-lab-target` | Docker Compose lab target setup (DVWA, etc.) |

Listed in [SKILLS.md](SKILLS.md).

## Agent workflows

### Run a demo engagement

Use the **run-engagement** skill. Summary:

1. Start lab target: `docker compose -f targets/dvwa/docker-compose.yml up -d`.
2. Verify scope file: `targets/dvwa/scope.yaml`.
3. Start orchestrator: `python -m spectre.cli run --target dvwa --scope lab`.
4. Start demo UI: `npm run dev` — connect to WebSocket at `ws://localhost:8765`.
5. Watch agents coordinate; halt with kill switch when done.
6. Export report: `python -m spectre.cli report --session <id>`.

### Add a new agent

Use the **add-agent** skill. Summary:

1. Define agent spec in `spectre/agents/<name>/` (prompt, tools, handoff rules).
2. Register in orchestrator agent registry.
3. Add handoff triggers in `spectre/orchestrator/handoffs.py`.
4. Add UI avatar and chat styling in `src/crew/`.
5. Add tests (1 positive + 3 negative) and `docs/local/local-agent-<name>.md`.

### Add a tool wrapper

Use the **add-tool-wrapper** skill. Summary:

1. Create sandboxed wrapper in `spectre/tools/<tool>.py` with scope check.
2. Register tool with relevant agent(s).
3. Parse output into Finding schema.
4. Add tests including out-of-scope rejection.
5. Document in `docs/local/local-tool-<name>.md`.

### Scaffold a new lab target

Use the **setup-lab-target** skill. Summary:

1. Add `targets/<name>/docker-compose.yml`.
2. Add `targets/<name>/scope.yaml` with explicit allowlist.
3. Add health check script.
4. Document in `docs/local/local-target-<name>.md`.

## Agent behavior

- **Lab only** — refuse to scan or exploit anything outside scope allowlist.
- **Bus-first** — agents publish findings to the bus; no direct agent-to-agent calls.
- **Explain handoffs** — every orchestrator activation includes a human-readable reason for the demo UI.
- **Test gate** — no feature ships without 1 positive + 3 negative tests passing.
- **Stop on red** — broken tests/build block all other work until fixed.
- **Document** — update `docs/local/` for every feature; keep README index current.
- **Smallest correct diff** — no cloud infra, C2 frameworks, or real-world target lists unless explicitly requested.
- **Research focus** — log coordination decisions for later analysis; handoff protocol is a first-class design artifact.

## Build phases

See [docs/local/local-plan-roadmap.md](docs/local/local-plan-roadmap.md) for the full roadmap.

| Phase | Goal | Demo milestone |
|-------|------|----------------|
| **0** | Docs, schemas, project scaffold | This documentation set |
| **1** | Findings Bus + Orchestrator + Recon agent | Recon populates timeline |
| **2** | VulnHunter + Exploiter + DVWA target | Agents hand off, first exploit |
| **3** | Reporter + demo UI | Full visual demo |
| **4** | Handoff research instrumentation | Export coordination logs for analysis |
