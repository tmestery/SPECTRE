---
name: add-agent
description: >-
  Adds or extends a SPECTRE agent role (Recon, VulnHunter, Exploiter, Reporter).
  Use when creating a new agent, updating prompts, tools, or handoff behavior.
---

# Add Agent

## Prerequisites

- Read [local-arch-agent-crew.md](../../../docs/local/local-arch-agent-crew.md)
- Read [local-arch-handoff-protocol.md](../../../docs/local/local-arch-handoff-protocol.md)
- GitHub issue open; branch created per **git-workflow**

## Steps

1. **Create agent module** at `spectre/agents/<name>/`:
   - `agent.py` — Agent class extending base
   - `prompt.md` — system prompt
   - `tools.yaml` — allowed tool list
   - `handoff.yaml` — publish types and hints

2. **Register** in `spectre/orchestrator/registry.py`

3. **Handoff rules** — add/update rules in `spectre/orchestrator/handoffs.py` if activation logic changes

4. **Tool access** — wire only tools listed in `tools.yaml`; enforce in agent base class

5. **UI** — add avatar/color in `src/crew/AgentAvatar.tsx` (Phase 3)

6. **Tests** — 1 positive + 3 negative in `tests/agents/test_<name>.py`:
   - Happy path with mock tool output
   - Out-of-scope rejection
   - Wrong tool refused
   - Max iterations / empty output handled

7. **Document** — `docs/local/local-agent-<name>.md`; index in README

## Checklist

- [ ] Agent does not call other agents directly (bus only)
- [ ] Prompt includes scope allowlist
- [ ] Findings use Pydantic schema
- [ ] agent_message published for demo UI
- [ ] Docs and tests complete
