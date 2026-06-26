# local-arch-llm-layer

**Status:** active
**Updated:** 2026-06-25
**Related:** `spectre/llm/`, `spectre/agents/routing/`, `spectre/agents/subagents/`

## Summary

SPECTRE agents run deterministic security tools first, then invoke **LLM-backed subagents** for analysis, triage, and narrative synthesis. Groq is the default provider via an OpenAI-compatible chat completions API.

## Architecture

```
Parent Agent (tool phase)
        │
        ▼
AgentCognitiveRouter ──► SubagentRegistry
        │                      │
        │                      ├─ surface_analyst (recon)
        │                      ├─ secret_triage (vuln_hunter)
        │                      ├─ cve_prioritizer (vuln_hunter)
        │                      ├─ threat_mapper (vuln_hunter)
        │                      ├─ validation_advisor (exploiter)
        │                      └─ executive_writer (reporter)
        ▼
LLMClient ──► Groq / OpenAI / Ollama (OpenAI-compatible)
        │
        ▼
Findings Bus (agent_message, NOTE findings, llm_invocation audit events)
```

## Components

| Path | Role |
|------|------|
| `spectre/llm/client.py` | Async chat completions client |
| `spectre/llm/router.py` | Per-task temperature / JSON mode routing |
| `spectre/llm/prompts.py` | Subagent system prompts |
| `spectre/agents/routing/router.py` | Parent-agent → subagent pipelines |
| `spectre/agents/subagents/` | Specialist LLM workers |

## Configuration

```env
LLM_PROVIDER=groq
GROQ_API_KEY=...
LLM_MODEL=llama-3.3-70b-versatile
LLM_ENABLED=true
```

Without `GROQ_API_KEY`, tools still run but subagent pipelines are skipped.

## Safety

- Scope allowlist included in every LLM user prompt
- Secrets only passed redacted in subagent context
- `llm_invocation` events audit provider, model, tokens, duration
- Subagents must not invent file paths or CVEs outside provided context

## Changelog

- **2026-06-25** — Initial LLM layer with six subagents and cognitive router pipelines.
