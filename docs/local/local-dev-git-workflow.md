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

### Issue tracker (selected)

Closed foundation (#1–#12, #14–#16, #22, #40) is summarized in [local-plan-roadmap.md](local-plan-roadmap.md). Active Phase 4+ work:

| Issue | Title | Notes |
|-------|-------|-------|
| [#13](https://github.com/tmestery/SPECTRE/issues/13) | Intentionally vulnerable sample repo | Open |
| [#28](https://github.com/tmestery/SPECTRE/issues/28) | Redesign demo dashboard UI | Open |
| [#29](https://github.com/tmestery/SPECTRE/issues/29)–[#34](https://github.com/tmestery/SPECTRE/issues/34) | Judging schemas, agents, orchestrator, UI | Open |
| [#35](https://github.com/tmestery/SPECTRE/issues/35) | Sync roadmap docs | This update |
| [#36](https://github.com/tmestery/SPECTRE/issues/36) | mypy typed CI | Open |
| [#37](https://github.com/tmestery/SPECTRE/issues/37) | A/B handoff thresholds | Open |
| [#38](https://github.com/tmestery/SPECTRE/issues/38) | `validation_failed_retry` handoff | Open |
| [#41](https://github.com/tmestery/SPECTRE/issues/41) | README refresh | End of wave |

## Tests

N/A — process policy.

## Changelog

- 2026-06-25 — Synced issue tracker with Phase 4+ work (#35)
- 2026-06-25 — CI workflow required for merge (#16)
- 2026-06-25 — Initial git workflow doc
