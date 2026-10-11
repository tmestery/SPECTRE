# local-agent-report-judge

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [local-arch-judging-agents.md](local-arch-judging-agents.md), issue #32

## Summary

Report Judge (`report_judge`) reviews `report_section` events against bus findings and publishes an advisory `report_verdict` (`accept` / `revise`).

## Implementation

- Path: `spectre/agents/report_judge/agent.py`
- Flags CVEs and backtick paths not present in finding evidence
- Does not rewrite reports; advisory only

## Tests

1 positive (accept backed report) + 3 negatives (invented CVE, out-of-scope, no sections).

## Changelog

- 2026-06-25 — Initial Report Judge (#32)
