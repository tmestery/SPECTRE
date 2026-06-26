# SPECTRE Skills

Project-specific Agent Skills live in `.cursor/skills/`. Use them for workflows; conventions remain in [AGENTS.md](AGENTS.md) and [.cursor/rules/project.mdc](.cursor/rules/project.mdc).

## Skills index

| Skill | Path | Use when |
|-------|------|----------|
| **development-standards** | [.cursor/skills/development-standards/](.cursor/skills/development-standards/) | Every feature, bugfix, refactor — lab scope, async I/O, 1+3 tests, stop on breakage |
| **document-feature** | [.cursor/skills/document-feature/](.cursor/skills/document-feature/) | Writing docs in `docs/local/` |
| **git-workflow** | [.cursor/skills/git-workflow/](.cursor/skills/git-workflow/) | Issues first, branch, PR to main — never commit directly to main |
| **add-agent** | [.cursor/skills/add-agent/](.cursor/skills/add-agent/) | New agent role or extending an existing agent |
| **add-tool-wrapper** | [.cursor/skills/add-tool-wrapper/](.cursor/skills/add-tool-wrapper/) | Sandboxed wrapper for nmap, nuclei, sqlmap, etc. |
| **run-engagement** | [.cursor/skills/run-engagement/](.cursor/skills/run-engagement/) | Full pen test run against a lab target |
| **setup-lab-target** | [.cursor/skills/setup-lab-target/](.cursor/skills/setup-lab-target/) | Docker Compose lab target (DVWA, etc.) |

## Documentation

All docs: [docs/local/](docs/local/) — naming pattern `local-<area>-<topic>.md`. Index: [docs/local/README.md](docs/local/README.md).

## Mandatory rules (summary)

1. **Lab targets only** — scope allowlist enforced on every tool invocation.
2. **Async I/O only** — never block the event loop or UI thread.
3. **1 positive + 3 negative tests** per new feature.
4. **Stop immediately** and fix if anything breaks before continuing.
5. **Document** every feature in `docs/local/`.
6. **Issue + PR** for every change — no direct commits to `main`.
