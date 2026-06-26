# local-safety-lab-scope

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [local-target-dvwa.md](local-target-dvwa.md), `spectre/safety/` (planned)

## Summary

SPECTRE is designed for **authorized lab environments only**. Scope enforcement, audit logging, and kill switches prevent accidental or intentional use against real-world targets.

## Context

Multi-agent pen testing with automated exploitation is high-risk if misused. Safety is architectural — not a disclaimer. Every tool invocation passes through scope checks; violations halt the engagement.

## Implementation

### Scope file format

```yaml
# targets/dvwa/scope.yaml
name: dvwa-lab
description: Local DVWA instance for SPECTRE demo
allowed_hosts:
  - 127.0.0.1
  - localhost
allowed_urls:
  - http://127.0.0.1:4280
  - http://localhost:4280
allowed_ports:
  - 4280
max_duration_minutes: 30
authorization: lab-local-only
```

### Enforcement points

| Layer | Check |
|-------|-------|
| CLI | Refuse `spectre run` without valid scope file |
| Orchestrator | Validate scope before agent activation |
| Tool wrapper | `safety.scope.check(target)` before subprocess |
| Agent prompt | Include allowlist; instruct refusal of out-of-scope |
| UI | Display scope banner; disable engagement start without scope |

### Audit log

Every tool invocation records:

```json
{
  "type": "tool_invocation",
  "tool": "nmap",
  "target": "127.0.0.1",
  "scope_check": "passed",
  "command_hash": "sha256:...",
  "exit_code": 0,
  "duration_ms": 4200,
  "timestamp": "..."
}
```

Stored in session event DB. Never log API keys or captured credentials in plaintext — redact in audit.

### Kill switch

- **CLI:** `spectre halt --session <id>`
- **UI:** Red "Halt Engagement" button → WebSocket `halt` message
- **Orchestrator:** Sets `halt_requested`; completes current tool then stops

### Prohibited (hard rules)

- Scanning IP ranges not in allowlist
- Using real-world domain lists (e.g. bug bounty targets) without explicit scope file authored for that engagement
- Committing `.env` with API keys
- Disabling scope checks in production code paths (test mocks only)

### Legal notice (README / UI)

SPECTRE is for **educational and authorized security research** on systems you own or have explicit permission to test. Users are responsible for compliance with applicable laws.

## Tests

| Case | Type |
|------|------|
| In-scope target passes check | Positive |
| Out-of-scope IP rejected | Negative |
| Out-of-scope URL rejected | Negative |
| Missing scope file aborts engagement | Negative |
| Kill switch halts within one tool completion | Negative |

## Changelog

- 2026-06-25 — Initial safety doc
