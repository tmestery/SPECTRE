# local-agent-recon

**Status:** draft  
**Updated:** 2026-06-25  
**Related:** [local-arch-agent-crew.md](local-arch-agent-crew.md), [local-target-dvwa.md](local-target-dvwa.md)

## Summary

The Recon agent performs discovery against in-scope targets — identifying hosts, open ports, services, and technology fingerprints. It is the first agent activated on engagement start.

## Context

Recon sets the foundation for all downstream agents. Output quality directly affects VulnHunter effectiveness. Recon must be thorough but bounded (max iterations, scope-limited).

## Implementation

### Responsibilities

- Port scan in-scope hosts (nmap)
- HTTP probing and title extraction (httpx)
- Technology fingerprinting (whatweb or httpx headers)
- Optional: directory enumeration (limited wordlist for demo)
- Publish `host`, `open_port`, `service`, `note` findings

### Tools

| Tool | Purpose | Output → Finding |
|------|---------|------------------|
| nmap | Port scan | `open_port`, `service` |
| httpx | HTTP probe | `service` (http metadata) |
| whatweb | Tech stack | `note` (tech fingerprint) |
| feroxbuster / ffuf | Dir enum (optional) | `note` (paths found) |

### Prompt highlights

- "You are the Recon agent. Discover attack surface on in-scope targets only."
- "Publish structured findings for every discovery. Cite tool output."
- "Do not attempt exploitation or vulnerability validation — hand off to VulnHunter."
- "Prefer speed for demo: scan only allowed ports; use `-T4` nmap timing."

### DVWA demo path

1. nmap `127.0.0.1 -p 4280` → `open_port: 4280/tcp`
2. httpx `http://127.0.0.1:4280` → Apache, PHP, DVWA title
3. Publish `service` finding with `handoff_hint: vuln_hunter`

### Handoff trigger

Orchestrator activates VulnHunter when [R1 discovery_sufficient](local-arch-handoff-protocol.md) fires.

### Agent message examples (demo UI)

> "Scanning 127.0.0.1 — found port 4280 open (HTTP). Running httpx for service details."

> "Target appears to be DVWA (Damn Vulnerable Web Application) on Apache/PHP. Handing off to VulnHunter."

## Tests

| Case | Type |
|------|------|
| Mock nmap output → valid open_port finding | Positive |
| Out-of-scope host rejected before nmap | Negative |
| Empty nmap output → no crash, optional note finding | Negative |
| Max iterations stops further tool calls | Negative |
| Recon refuses sqlmap/nuclei tools | Negative |

## Changelog

- 2026-06-25 — Initial Recon agent doc
