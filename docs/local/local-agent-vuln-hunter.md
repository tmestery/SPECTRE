# local-agent-vuln-hunter

**Status:** draft  
**Updated:** 2026-06-25  
**Related:** [local-agent-recon.md](local-agent-recon.md), [local-agent-exploiter.md](local-agent-exploiter.md)

## Summary

The VulnHunter agent identifies security weaknesses on discovered services — misconfigurations, known CVEs, and application-level vulnerabilities (SQLi, XSS, etc.). It publishes `vulnerability` findings with exploitability scores for handoff to Exploiter.

## Context

VulnHunter bridges discovery and exploitation. It validates that services are interesting but does not run full exploits (that's Exploiter's job). False positives are acceptable at `tentative` status; Exploiter confirms.

## Implementation

### Responsibilities

- Run vulnerability scanners against in-scope web services
- Perform targeted probes based on Recon findings (e.g. DVWA sqli endpoint)
- Score exploitability (0.0–1.0) for handoff threshold
- Publish `vulnerability` findings with evidence and `related_ids` to Recon findings

### Tools

| Tool | Purpose | Output |
|------|---------|--------|
| nuclei | Template-based vuln scan | `vulnerability` |
| nikto | Web server misconfig scan | `vulnerability`, `note` |
| custom probes | DVWA-specific paths | `vulnerability` |

### Exploitability scoring (v1 heuristic)

| Score | Criteria |
|-------|----------|
| 0.9–1.0 | Known exploitable class (SQLi, RCE gadget) with exposed endpoint |
| 0.7–0.9 | Likely vuln with partial evidence (error-based SQLi indicator) |
| 0.4–0.6 | Potential issue needing confirmation |
| < 0.4 | Informational, no handoff to Exploiter |

### DVWA demo path

1. nuclei against `http://127.0.0.1:4280` with OWASP templates
2. Probe `/vulnerabilities/sqli/` — error-based SQLi indicator
3. Publish `vulnerability`: SQL injection, exploitability 0.85, `handoff_hint: exploiter`

### Prompt highlights

- "You are VulnHunter. Identify vulnerabilities; do not exploit."
- "Set exploitability score honestly. Tentative findings are OK."
- "Link each vulnerability to Recon finding IDs in related_ids."

### Handoff trigger

[R2 exploitable_vuln_found](local-arch-handoff-protocol.md) when exploitability ≥ 0.7.

## Tests

| Case | Type |
|------|------|
| Mock nuclei output → vulnerability finding with score | Positive |
| Out-of-scope URL rejected | Negative |
| Low exploitability finding does not trigger exploiter handoff | Negative |
| VulnHunter refuses sqlmap | Negative |
| Malformed scanner output handled gracefully | Negative |

## Changelog

- 2026-06-25 — Initial VulnHunter agent doc
