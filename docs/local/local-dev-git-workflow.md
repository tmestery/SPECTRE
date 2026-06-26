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
5. Merge only after review and green checks.

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

### Suggested initial issues (Phase 0–1)

| Issue | Title |
|-------|-------|
| #1 | Scaffold Python + UI monorepo |
| #2 | Implement Findings Bus and schemas |
| #3 | Scope enforcement and audit log |
| #4 | Recon agent and nmap wrapper |
| #5 | Handoff protocol v1 |
| #6 | VulnHunter agent |
| #7 | Exploiter agent |
| #8 | DVWA Docker target |
| #9 | Reporter agent |
| #10 | Demo UI shell |
| #11 | WebSocket event stream |
| #12 | Report export |

## Tests

N/A — process policy.

## Changelog

- 2026-06-25 — Initial git workflow doc
