# local-dev-git-workflow

**Status:** active  
**Updated:** 2026-06-25  
**Related:** `.cursor/skills/git-workflow/SKILL.md`, [local-dev-standards.md](local-dev-standards.md)

## Summary

All SPECTRE work flows through GitHub issues and pull requests. No direct commits to `main`.

## Context

Enforced in `.cursor/rules/project.mdc`, **git-workflow** skill, and [AGENTS.md](../../AGENTS.md). GitHub issue and PR templates live in `.github/`.

## Implementation

### Required flow

```
Issue → branch → commits → PR → review → merge
```

1. Create a GitHub issue for every change (feature, fix, chore, research).
2. Branch from `main`: `feature|fix|chore/<issue>-<slug>`.
3. Make focused commits with clear imperative messages.
4. Open PR against `main`; body includes summary, test plan, `Closes #<n>`.
5. Merge only after review and green CI checks ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml): ruff, pytest, vitest, UI build).

### Branch naming

| Prefix | Use |
|--------|-----|
| `feature/` | New functionality |
| `fix/` | Bug fixes |
| `chore/` | Docs, config, tooling |
| `research/` | Handoff experiments, instrumentation |

Example: `feature/4-recon-agent`

### Commit hygiene

- Small, logical commits — one concern per commit
- Imperative subject lines; reference issue when useful
- No secrets, no `node_modules/`, `dist/`, `.venv/`, or session data
- Pull latest `main` before branching and before opening PR

### PR requirements

- Must link to an issue
- Must describe what changed and how to test
- Must meet **development-standards** (tests, docs, scope rules)
- Security-sensitive changes: note scope/safety impact in PR body

### Issue tracker (#1–#16)

| Issue | Title | Phase |
|-------|-------|-------|
| [#1](https://github.com/tmestery/SPECTRE/issues/1) | Phase 0: documentation and agent scaffold | 0 |
| [#2](https://github.com/tmestery/SPECTRE/issues/2) | Scaffold Python + UI monorepo | 1 |
| [#3](https://github.com/tmestery/SPECTRE/issues/3) | Findings Bus and repo finding schemas | 1 |
| [#4](https://github.com/tmestery/SPECTRE/issues/4) | Repo scope enforcement and audit log | 1 |
| [#5](https://github.com/tmestery/SPECTRE/issues/5) | Orchestrator skeleton and engagement lifecycle | 1 |
| [#6](https://github.com/tmestery/SPECTRE/issues/6) | Recon agent and GitHub API client | 1 |
| [#7](https://github.com/tmestery/SPECTRE/issues/7) | Handoff protocol v1 (repo rules) | 1–2 |
| [#8](https://github.com/tmestery/SPECTRE/issues/8) | VulnHunter agent with gitleaks and osv-scanner | 2 |
| [#9](https://github.com/tmestery/SPECTRE/issues/9) | Exploiter agent and validation layer | 2 |
| [#10](https://github.com/tmestery/SPECTRE/issues/10) | Reporter agent and GitHub permalink reports | 3 |
| [#11](https://github.com/tmestery/SPECTRE/issues/11) | Demo UI shell | 3 |
| [#12](https://github.com/tmestery/SPECTRE/issues/12) | WebSocket event stream and kill switch | 3 |
| [#13](https://github.com/tmestery/SPECTRE/issues/13) | Intentionally vulnerable sample repo for demos | 4 |
| [#14](https://github.com/tmestery/SPECTRE/issues/14) | Handoff decision logging and coordination metrics | 4 |
| [#15](https://github.com/tmestery/SPECTRE/issues/15) | Engagement replay mode | 4 |
| [#16](https://github.com/tmestery/SPECTRE/issues/16) | CI pipeline for tests and lint | dev |

## Tests

N/A — process policy.

## Changelog

- 2026-06-25 — CI workflow required for merge (#16)

- 2026-06-25 — Initial git workflow doc
