# local-arch-findings-bus

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [local-arch-handoff-protocol.md](local-arch-handoff-protocol.md), `spectre/schemas/finding.py` (planned)

## Summary

The Findings Bus is SPECTRE's shared memory — an append-only event store where agents publish structured findings and subscribe to relevant updates. It is the single source of truth for engagement state, handoff decisions, and report generation.

## Context

Direct agent-to-agent messaging is intentionally avoided. The bus pattern provides:

- **Auditability** — full engagement replay from event log
- **Decoupling** — agents don't need to know about each other
- **Research data** — handoff inputs are queryable
- **UI streaming** — same events feed the demo timeline

## Implementation

### Event types

| Type | Publisher | Purpose |
|------|-----------|---------|
| `engagement_started` | Orchestrator | Session metadata, scope snapshot |
| `agent_activated` | Orchestrator | Which agent, why, input finding IDs |
| `agent_message` | Any agent | Human-readable summary for demo UI |
| `finding` | Any agent | Structured discovery/vuln/exploit data |
| `handoff_decision` | Orchestrator | Rule fired, inputs, outcome |
| `tool_invocation` | Tool layer | Audit: tool, target, exit code, duration |
| `engagement_halted` | Orchestrator/UI | Kill switch, reason |
| `report_section` | Reporter | Report building blocks |
| `engagement_complete` | Orchestrator | Final status, report path |

### Finding schema

```python
# spectre/schemas/finding.py (planned)
class Finding(BaseModel):
    id: str                    # fnd_<ulid>
    type: FindingType          # host | open_port | service | vulnerability | exploit_attempt | credential | note
    agent: str                 # recon | vuln_hunter | exploiter | reporter
    target: str                # URL or host:port
    severity: Severity         # info | low | medium | high | critical
    confidence: float          # 0.0 – 1.0
    title: str
    description: str | None
    evidence: dict             # tool-specific structured output
    related_ids: list[str]     # upstream finding IDs
    handoff_hint: str | None   # suggested next agent
    status: FindingStatus      # tentative | confirmed | false_positive | exploited
    created_at: datetime
```

### Severity mapping (v1)

| Severity | Examples |
|----------|----------|
| `info` | Open port, service banner, directory listing |
| `low` | Version disclosure, missing security header |
| `medium` | Reflected XSS, weak session config |
| `high` | SQLi, auth bypass, RCE PoC |
| `critical` | Confirmed RCE with data exfil (lab only) |

### Storage

**v1:** SQLite per engagement session at `data/sessions/<session_id>/events.db`.

Tables:

- `events` — id, type, payload (JSON), timestamp, sequence_num
- `findings` — materialized view / index on `finding` events for fast query

**Pub/Sub:** In-process async queue; subscribers filter by event type and finding attributes.

```python
# Conceptual API
await bus.publish(event)
findings = await bus.query(type="vulnerability", status="confirmed")
async for event in bus.subscribe(types=["finding", "agent_message"]):
    await ws.broadcast(event)
```

### Query patterns

| Consumer | Query |
|----------|-------|
| VulnHunter on activation | All `open_port` + `service` for in-scope hosts |
| Exploiter on activation | All `vulnerability` where exploitability ≥ threshold |
| Reporter on activation | All findings, grouped by severity |
| Handoff engine | Count by type/status since last agent completion |
| Demo UI | All events, chronological |

### WebSocket payload

Events serialize to JSON for UI consumption. Large evidence blobs truncated in stream; full evidence available on click via REST `GET /api/sessions/:id/findings/:fnd_id`.

## Tests

| Case | Type |
|------|------|
| Publish and retrieve finding by ID | Positive |
| Reject finding with invalid schema | Negative |
| Query filters return correct subset | Negative |
| Subscriber receives only matching event types | Negative |
| Sequence numbers are monotonic | Negative |

## Changelog

- 2026-06-25 — Initial bus design
