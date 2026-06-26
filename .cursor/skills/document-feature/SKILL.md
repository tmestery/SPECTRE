---
name: document-feature
description: >-
  Writes and updates SPECTRE local documentation in docs/local/ using the
  project naming convention. Use when adding a feature, changing architecture,
  or recording decisions — required alongside every feature.
---

# Document Feature

All project documentation lives in `docs/local/`. Create or update a doc as part of every feature — not as an afterthought.

## Naming convention

```
docs/local/local-<area>-<topic>.md
```

| Area | Values | Example |
|------|--------|---------|
| `arch` | architecture, coordination | `local-arch-findings-bus` |
| `dev` | standards, tooling | `local-dev-standards` |
| `agent` | agent roles | `local-agent-recon` |
| `tool` | tool wrappers | `local-tool-nmap` |
| `target` | lab targets | `local-target-dvwa` |
| `ui` | demo dashboard | `local-ui-demo-dashboard` |
| `safety` | scope, audit | `local-safety-lab-scope` |
| `test` | testing | `local-test-strategy` |
| `plan` | roadmap | `local-plan-roadmap` |

## Document template

```markdown
# local-<area>-<topic>

**Status:** draft | active | deprecated
**Updated:** YYYY-MM-DD
**Related:** paths, issues, or feature names

## Summary
## Context
## Implementation
## Tests
## Changelog
```

## Rules

- One doc per feature or cohesive subsystem; split if > ~150 lines.
- Update **Updated** and **Changelog** on every edit.
- Cross-link related docs and source paths.
- Index new docs in [docs/local/README.md](../../../docs/local/README.md).
