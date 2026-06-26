# local-agent-vuln-hunter

**Status:** draft  
**Updated:** 2026-06-25  
**Related:** [local-agent-recon.md](local-agent-recon.md), [local-agent-exploiter.md](local-agent-exploiter.md)

## Summary

The VulnHunter agent hunts for secrets, vulnerable dependencies, and misconfigurations in an authorized GitHub repo — publishing findings for Exploiter to validate.

## Context

VulnHunter consumes Recon's inventory to run targeted scans. It reports tentative findings; Exploiter confirms impact.

## Implementation

### Responsibilities

- Run gitleaks on cloned repo (including git history per `max_commits_depth`)
- Run osv-scanner on dependency manifests
- Analyze GitHub Actions workflows for unsafe patterns
- Flag committed configs (`.env`, credentials, debug flags)
- Publish `secret`, `vulnerability`, `misconfiguration` findings

### Tools

| Tool | Purpose | Output |
|------|---------|--------|
| gitleaks | Secret detection in code + history | `secret` |
| osv-scanner | CVE lookup for deps | `vulnerability` |
| workflow analyzer | `pull_request_target`, unpinned actions | `misconfiguration` |
| semgrep (Phase 2) | Static patterns | `vulnerability` |

### Confidence / exploitability

| Finding | Score driver |
|---------|--------------|
| Secret | Rule match strength, entropy, file path sensitivity |
| CVE | CVSS, direct vs transitive dep, usage in code |
| Workflow | Known dangerous pattern (e.g. PRT with checkout of PR head) |

### Demo path

1. gitleaks on clone → secret in history (or planted in sample repo)
2. osv-scanner on `package-lock.json` → CVE
3. Workflow check → unpinned `actions/checkout@v3`
4. Hand off highest-confidence finding to Exploiter

### Handoff trigger

[R2 actionable_finding](local-arch-handoff-protocol.md)

## Tests

| Case | Type |
|------|------|
| Mock gitleaks output → secret finding | Positive |
| Out-of-scope repo rejected | Negative |
| Low-confidence secret does not trigger exploiter | Negative |
| VulnHunter refuses live token validation | Negative |
| Malformed scanner output handled | Negative |

## Changelog

- 2026-06-25 — Rewrote for repo secret/CVE hunting
- 2026-06-25 — Initial VulnHunter agent doc
