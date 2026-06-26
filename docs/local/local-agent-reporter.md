# local-agent-reporter

**Status:** active  
**Updated:** 2026-06-26  
**Related:** [local-target-github-repo.md](local-target-github-repo.md), [local-ui-demo-dashboard.md](local-ui-demo-dashboard.md)

## Summary

The Reporter agent synthesizes all bus findings into a **repository security report** — executive summary, findings table with GitHub permalinks, remediation steps, and agent coordination log.

## Context

Reporter is read-only. Output is suitable for sharing with repo maintainers and doubles as the demo's payoff screen.

## Implementation

### Report structure

```markdown
# SPECTRE Repository Security Report

**Target:** tmestery/my-app @ main
**Scanned:** 2026-06-25

## Executive Summary

## Scope
[From scopes/*.yaml]

## Findings Summary
| ID | Severity | Type | Location | Status |

## Detailed Findings
### FND-001: AWS key in git history
**File:** src/config.ts:14 · [View on GitHub](permalink)
**Remediation:** Rotate key, purge from history with git-filter-repo

## Agent Coordination Log
[Handoff decisions]

## Remediation Priority
1. Rotate exposed credentials
2. Patch CVE-XXXX in dependency X
```

### Export formats

| Format | Path |
|--------|------|
| Markdown | `reports/<session_id>.md` |
| HTML | `reports/<session_id>.html` |
| SARIF (Phase 2) | `reports/<session_id>.sarif` |

### GitHub permalinks

Reporter generates `https://github.com/owner/repo/blob/<commit>/path#Lline` links from finding evidence.

## Tests

| Case | Type |
|------|------|
| Mock findings → valid markdown with permalinks | Positive |
| Empty findings → clean report | Negative |
| Secrets redacted in report output | Negative |
| Duplicates deduplicated | Negative |
| Missing session raises clear error | Negative |

## Changelog

- 2026-06-25 — Updated for repo security reports with GitHub links
- 2026-06-25 — Initial Reporter agent doc
