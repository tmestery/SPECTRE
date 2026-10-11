# local-agent-finding-judge

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [local-arch-judging-agents.md](local-arch-judging-agents.md), issue #30

## Summary

Finding Judge (`finding_judge`) batch-reviews secret, vulnerability, and misconfiguration findings and publishes advisory `judgment` findings (`uphold` / `downgrade` / `dismiss`).

## Context

Part of the judging layer ADR. Orchestrator scheduling after VulnHunter/Exploiter is tracked in #33; this agent is registered and runnable now.

## Implementation

| Item | Value |
|------|-------|
| Path | `spectre/agents/finding_judge/agent.py` |
| Tools | None (read-only bus) |
| Max iterations | 3 |
| LLM | Optional polish of verdict/rationale; deterministic fallback when disabled |

### Deterministic rules (v1)

- Secret confidence ≥ 0.8 → `uphold`
- Secret confidence < 0.5 → `dismiss`
- Secret otherwise → `downgrade`
- CVE exploitability ≥ 0.7 → `uphold`, else `downgrade`
- Misconfig high/critical → `uphold`, else `downgrade`

Out-of-scope engagement repo → `blocked`. Out-of-scope finding targets are skipped. Existing judgments are not duplicated.

## Tests

| Case | Type |
|------|------|
| High-confidence secret → uphold | Positive |
| Out-of-scope engagement blocked | Negative |
| Out-of-scope finding target skipped | Negative |
| Existing judgment not duplicated | Negative |

## Changelog

- 2026-06-25 — Initial Finding Judge agent (#30)
