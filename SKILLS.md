# SPECTRE Skills

Project-specific Agent Skills live in `.cursor/skills/`. Use them for workflows; conventions remain in [AGENTS.md](AGENTS.md) and [.cursor/rules/project.mdc](.cursor/rules/project.mdc).

## Skills index

| Skill | Path | Use when |
|-------|------|----------|
| **development-standards** | [.cursor/skills/development-standards/](.cursor/skills/development-standards/) | Every feature — repo scope, async I/O, 1+3 tests |
| **document-feature** | [.cursor/skills/document-feature/](.cursor/skills/document-feature/) | Writing docs in `docs/local/` |
| **git-workflow** | [.cursor/skills/git-workflow/](.cursor/skills/git-workflow/) | Issues first, branch, PR to main |
| **add-agent** | [.cursor/skills/add-agent/](.cursor/skills/add-agent/) | New or extended agent role |
| **add-tool-wrapper** | [.cursor/skills/add-tool-wrapper/](.cursor/skills/add-tool-wrapper/) | GitHub API, gitleaks, osv-scanner, etc. |
| **run-engagement** | [.cursor/skills/run-engagement/](.cursor/skills/run-engagement/) | Full repo audit run |
| **setup-repo-scope** | [.cursor/skills/setup-repo-scope/](.cursor/skills/setup-repo-scope/) | Scope files for authorized repos |

## Mandatory rules (summary)

1. **Authorized repos only** — `allowed_repos` enforced on every scan.
2. **Async I/O only** — never block the event loop or UI thread.
3. **1 positive + 3 negative tests** per new feature.
4. **Stop immediately** and fix if anything breaks.
5. **Document** every feature in `docs/local/`.
6. **Issue + PR** for every change.
