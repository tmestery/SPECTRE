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
| `tool` | Security tool wrappers (gitleaks, GitHub API, etc.) |
| `target` | GitHub repos, sample repos |
| `ui` | Demo dashboard, streaming, visualization |
| `safety` | Repo scope enforcement, audit, redaction |
| `test` | Testing strategy, fixtures, patterns |
| `plan` | Roadmap, milestones, research goals |

## Index

| Document | Description |
|----------|-------------|
| [local-plan-roadmap.md](local-plan-roadmap.md) | Master build plan, phases, milestones |
| [local-arch-overview.md](local-arch-overview.md) | System architecture and folder layout |
| [local-arch-agent-crew.md](local-arch-agent-crew.md) | Four-agent crew design |
| [local-arch-findings-bus.md](local-arch-findings-bus.md) | Shared memory, event schema, pub/sub |
| [local-arch-handoff-protocol.md](local-arch-handoff-protocol.md) | Coordination and handoff rules |
| [local-arch-handoff-profiles.md](local-arch-handoff-profiles.md) | A/B handoff threshold profiles |
| [local-arch-judging-agents.md](local-arch-judging-agents.md) | Judging agent layer ADR (advisory v1) |
| [local-research-metrics.md](local-research-metrics.md) | Handoff JSONL + coordination metrics export |
| [local-research-replay.md](local-research-replay.md) | Paced engagement replay from event log |
| [local-arch-llm-layer.md](local-arch-llm-layer.md) | LLM client, routers, and subagents |
| [local-arch-orchestrator.md](local-arch-orchestrator.md) | Crew loop, engagement lifecycle |
| [local-arch-tech-stack.md](local-arch-tech-stack.md) | Python, React, GitHub API, Groq |
| [local-dev-standards.md](local-dev-standards.md) | Async I/O, tests, documentation rules |
| [local-dev-readme.md](local-dev-readme.md) | Root README maintenance notes |
| [local-dev-git-workflow.md](local-dev-git-workflow.md) | Issues, branches, PRs |
| [local-dev-github-templates.md](local-dev-github-templates.md) | `.github/` PR/issue templates and CI layout |
| [local-dev-repo-layout.md](local-dev-repo-layout.md) | Root hygiene, branding under `docs/assets/` |
| [local-safety-lab-scope.md](local-safety-lab-scope.md) | Repo allowlists, audit, redaction |
| [local-target-github-repo.md](local-target-github-repo.md) | **Primary v1 target** — GitHub repo audits |
| [local-target-vuln-sample.md](local-target-vuln-sample.md) | Intentionally vulnerable demo sample repo |
| [local-target-dvwa.md](local-target-dvwa.md) | ~~DVWA Docker lab~~ (deprecated) |
| [local-agent-recon.md](local-agent-recon.md) | Recon — repo mapping |
| [local-agent-vuln-hunter.md](local-agent-vuln-hunter.md) | VulnHunter — secrets, CVEs, workflows |
| [local-agent-exploiter.md](local-agent-exploiter.md) | Exploiter — finding validation |
| [local-agent-reporter.md](local-agent-reporter.md) | Reporter — repo security report |
| [local-agent-finding-judge.md](local-agent-finding-judge.md) | Finding Judge — advisory judgment findings |
| [local-agent-handoff-judge.md](local-agent-handoff-judge.md) | Handoff Judge — advisory handoff verdicts |
| [local-agent-report-judge.md](local-agent-report-judge.md) | Report Judge — advisory report verdicts |
| [local-ui-demo-dashboard.md](local-ui-demo-dashboard.md) | Demo UI design |
| [local-tool-websocket-stream.md](local-tool-websocket-stream.md) | WebSocket event stream + halt |
| [local-test-strategy.md](local-test-strategy.md) | pytest, vitest, fixtures |
| [local-dev-docker.md](local-dev-docker.md) | Docker Compose one-command demo |
| [local-dev-release.md](local-dev-release.md) | Version bump checklist and GitHub Releases |

## Adding docs

1. Name file `local-<area>-<topic>.md`.
2. Use the template in `.cursor/skills/document-feature/SKILL.md`.
3. Add a row to the index table above.
4. Set **Updated** date and **Changelog** entry in the doc.
