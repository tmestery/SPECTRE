# local-agent-handoff-judge

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [local-arch-judging-agents.md](local-arch-judging-agents.md), issue #31

## Summary

Handoff Judge (`handoff_judge`) reviews unpublished `handoff_decision` events and emits advisory `handoff_verdict` events (`approve` / `defer` / `reject`). v1 does not block orchestrator transitions.

## Implementation

- Path: `spectre/agents/handoff_judge/agent.py`
- Registered in `AgentRegistry`; scheduling in #33
- Skips decisions that already have a verdict for the same `decision_id`

## Tests

1 positive (approve `repo_mapped`) + 3 negatives (out-of-scope, empty, already judged).

## Changelog

- 2026-06-25 — Initial Handoff Judge (#31)
