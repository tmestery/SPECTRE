# local-agent-reporter

**Status:** draft  
**Updated:** 2026-06-25  
**Related:** [local-arch-findings-bus.md](local-arch-findings-bus.md), [local-ui-demo-dashboard.md](local-ui-demo-dashboard.md)

## Summary

The Reporter agent synthesizes all bus findings into a structured penetration test report — executive summary, findings table, evidence appendix, and remediation recommendations.

## Context

Reporter is read-only on tools (no offensive capabilities). It runs once at engagement end (or on timeout). Output feeds the demo UI live report panel and exportable artifacts.

## Implementation

### Responsibilities

- Query all findings for the engagement
- Deduplicate and group related findings
- Generate executive summary (non-technical audience)
- Build findings table: severity, title, status, remediation
- Publish `report_section` events for streaming UI
- Write final artifacts: `reports/<session_id>.md`, `.html`

### Report structure

```markdown
# SPECTRE Penetration Test Report

## Executive Summary
[2–3 paragraphs]

## Scope
[From scope.yaml]

## Methodology
Recon → VulnHunter → Exploiter (automated agent crew)

## Findings Summary
| ID | Severity | Title | Status |
|----|----------|-------|--------|

## Detailed Findings
### FND-001: SQL Injection in DVWA
...

## Agent Coordination Log
[Handoff decisions summary — research section]

## Remediation Recommendations
...

## Appendix: Evidence
...
```

### Prompt highlights

- "You are Reporter. Synthesize findings; do not speculate beyond evidence."
- "Include handoff timeline for research transparency."
- "Remediation must be actionable and specific."

### Tools

- Read-only bus query API
- Jinja2 or markdown templates in `spectre/agents/reporter/templates/`

### Export formats

| Format | Path |
|--------|------|
| Markdown | `reports/<session_id>.md` |
| HTML | `reports/<session_id>.html` |
| JSON | `reports/<session_id>.json` (machine-readable) |

## Tests

| Case | Type |
|------|------|
| Mock findings → valid markdown report | Positive |
| Empty findings → report with "no issues" section | Negative |
| Duplicate findings deduplicated | Negative |
| Report excludes out-of-scope findings | Negative |
| Missing session ID raises clear error | Negative |

## Changelog

- 2026-06-25 — Initial Reporter agent doc
