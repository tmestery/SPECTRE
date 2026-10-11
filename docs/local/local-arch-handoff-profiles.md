# local-arch-handoff-profiles

**Status:** active  
**Updated:** 2026-10-10  
**Related:** [local-arch-handoff-protocol.md](local-arch-handoff-protocol.md), [local-research-metrics.md](local-research-metrics.md), issue #37

## Summary

Handoff confidence and severity thresholds are loaded from named YAML profiles so research A/B runs can swap bars without code changes.

## Context

v1 used hard-coded thresholds (`secret ≥ 0.8`, `exploitability ≥ 0.7`, misconfig `high|critical`). Experiments need a stricter profile without forking the orchestrator.

## Implementation

### Profiles

| File | Name | Notes |
|------|------|-------|
| `handoff_profiles/default.yaml` | `default` | Historical v1 thresholds |
| `handoff_profiles/strict.yaml` | `strict` | Higher bars; fewer Exploiter activations |

Fields: `secret_confidence_min`, `vulnerability_exploitability_min`, `misconfiguration_severities`.

### Loading

- `spectre/orchestrator/profiles.py` — `load_handoff_profile(name)`
- Settings: `HANDOFF_PROFILE` (default `default`), `HANDOFF_PROFILES_DIR`
- CLI: `python -m spectre.cli run ... --handoff-profile strict`
- `Engagement.handoff_profile` is resolved at start; name is published on `engagement_started`

### Metrics

`metrics.json` includes `handoff_profile` taken from the `engagement_started` payload.

## Tests

| Case | Type |
|------|------|
| Default profile hands off mid-high secret | Positive |
| Strict profile routes same secret to reporter | Negative |
| Missing profile file raises | Negative |
| Empty profile name raises | Negative |
| Non-mapping YAML raises | Negative |
| Metrics record profile name | Positive (metrics) |

## Changelog

- 2026-10-10 — Initial handoff profiles (`default`, `strict`) (#37)
