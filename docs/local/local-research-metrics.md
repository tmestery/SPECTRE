# local-research-metrics

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [local-arch-handoff-protocol.md](local-arch-handoff-protocol.md), [local-plan-roadmap.md](local-plan-roadmap.md), issue #14

## Summary

SPECTRE exports per-session coordination artifacts for research: a JSONL stream of every `handoff_decision` and a `metrics.json` summary of timing, finding volume, and validation outcomes.

## Context

Phase 4 studies how agents coordinate. The Findings Bus remains the source of truth; exports are derived views written under the session data directory.

## Implementation

### Artifacts

| File | Location | Contents |
|------|----------|----------|
| `handoffs.jsonl` | `data/sessions/<id>/` | One JSON object per `handoff_decision` event |
| `metrics.json` | `data/sessions/<id>/` | Aggregated coordination metrics |

### Metrics fields

| Field | Meaning |
|-------|---------|
| `time_to_first_finding_seconds` | Seconds from `engagement_started` to first `finding` event (`null` if none) |
| `time_to_handoff` | List of `{rule, from_agent, to_agent, seconds_from_start, input_finding_ids}` |
| `findings_per_agent` | Count of findings keyed by publishing agent |
| `false_positive_rate` | `false_positive / (confirmed + false_positive)` over `validation_attempt` findings (`null` if none) |
| `handoff_counts_by_rule` | Count of handoff decisions by rule name |
| `validation_confirmed` / `validation_false_positive` | Raw validation counts |
| `total_findings` / `total_handoffs` | Totals |
| `judgment_count` | Count of `judgment` findings |
| `handoff_verdict_count` / `report_verdict_count` | Advisory judge verdict events |

### CLI

```bash
python -m spectre.cli metrics --session eng_<id>
# optional: --output /path/to/dir
```

Prints paths plus a JSON summary. Recomputes from `events.db` (safe to re-run).

### Auto-export

When an engagement finishes, the orchestrator writes the same artifacts to the session directory (best-effort; failures are logged and do not fail the engagement).

### Module

- `spectre/research/metrics.py` — `compute_metrics`, `export_session_metrics`

## Tests

| Case | Type |
|------|------|
| Happy path with handoffs + FP rate | Positive |
| Empty event list raises | Negative |
| Missing `engagement_started` raises | Negative |
| Session with no handoffs / no validations | Negative |

## Changelog

- 2026-06-25 — Initial coordination metrics export (#14)
