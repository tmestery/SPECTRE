# docs/local — SPECTRE local documentation

Project documentation index. All docs use this naming convention:

```
local-<area>-<topic>.md
```

| Area | Use for |
|------|---------|
| `arch` | Architecture, system design, coordination protocols |
| `dev` | Development standards, tooling, git workflow |
| `agent` | Individual agent roles, prompts, tool access |
| `tool` | Security tool wrappers (nmap, nuclei, etc.) |
| `target` | Lab targets (DVWA, Juice Shop) |
| `ui` | Demo dashboard, streaming, visualization |
| `safety` | Scope enforcement, audit, legal guardrails |
| `test` | Testing strategy, fixtures, patterns |
| `plan` | Roadmap, milestones, research goals |

## Index

| Document | Description |
|----------|-------------|
| [local-plan-roadmap.md](local-plan-roadmap.md) | Master build plan, phases, milestones, research goals |
| [local-arch-overview.md](local-arch-overview.md) | System architecture and folder layout |
| [local-arch-agent-crew.md](local-arch-agent-crew.md) | Four-agent crew design and responsibilities |
| [local-arch-findings-bus.md](local-arch-findings-bus.md) | Shared memory, event schema, pub/sub |
| [local-arch-handoff-protocol.md](local-arch-handoff-protocol.md) | Coordination, activation rules, research instrumentation |
| [local-arch-orchestrator.md](local-arch-orchestrator.md) | Crew loop, scheduling, engagement lifecycle |
| [local-arch-tech-stack.md](local-arch-tech-stack.md) | Python, React, Docker, LLM integration choices |
| [local-dev-standards.md](local-dev-standards.md) | Async I/O, tests, stop-on-break, documentation rules |
| [local-dev-git-workflow.md](local-dev-git-workflow.md) | Issues, branches, PRs, commit hygiene |
| [local-safety-lab-scope.md](local-safety-lab-scope.md) | Scope allowlists, audit log, kill switch |
| [local-agent-recon.md](local-agent-recon.md) | Recon agent — discovery, tools, handoff triggers |
| [local-agent-vuln-hunter.md](local-agent-vuln-hunter.md) | VulnHunter agent — vulnerability identification |
| [local-agent-exploiter.md](local-agent-exploiter.md) | Exploiter agent — PoC exploitation |
| [local-agent-reporter.md](local-agent-reporter.md) | Reporter agent — synthesis and report output |
| [local-target-dvwa.md](local-target-dvwa.md) | DVWA Docker lab target setup and demo path |
| [local-ui-demo-dashboard.md](local-ui-demo-dashboard.md) | Demo UI — agent chat, timeline, handoff graph |
| [local-test-strategy.md](local-test-strategy.md) | pytest, vitest, integration test patterns |

## Adding docs

1. Name file `local-<area>-<topic>.md`.
2. Use the template in `.cursor/skills/document-feature/SKILL.md`.
3. Add a row to the index table above.
4. Set **Updated** date and **Changelog** entry in the doc.
