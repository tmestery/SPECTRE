# local-arch-tech-stack

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [local-plan-roadmap.md](local-plan-roadmap.md), [local-target-github-repo.md](local-target-github-repo.md)

## Summary

Technology choices for SPECTRE v1 — Python orchestration, GitHub API integration, repo scanning tools, React demo UI, SQLite event store, and Groq-powered tool-calling agents.

## Implementation

### Stack overview

| Layer | Technology | Notes |
|-------|------------|-------|
| Orchestration | Python 3.12+ | asyncio, Pydantic v2 |
| GitHub | PyGithub or `httpx` + REST | Clone, contents, workflows |
| Secret scan | gitleaks | Async subprocess on clone |
| CVE scan | osv-scanner | Dependency manifests |
| LLM | **Groq** default | `llama-3.3-70b-versatile`; OpenAI-compatible API |
| Event store | SQLite | Per-session at `data/sessions/<id>/` |
| WebSocket | FastAPI or `websockets` | Stream bus events to UI |
| Demo UI | Vite + React 18 + TypeScript | SanFran3D conventions |
| Scope config | YAML in `scopes/` | `allowed_repos` allowlist |
| Python tests | pytest + pytest-asyncio | Mock GitHub + scanner fixtures |
| Frontend tests | Vitest | Colocated `*.test.ts` |

### Security tools (wrapped)

| Tool | Agent | Purpose |
|------|-------|---------|
| GitHub API | Recon | Metadata, contents, workflows |
| gitleaks | VulnHunter | Secrets in code and history |
| osv-scanner | VulnHunter | Dependency CVEs |
| workflow parser | VulnHunter | Actions misconfigs |
| token validators | Exploiter | Read-only secret validation |

All tools: async subprocess or async HTTP, repo scope check, timeout, audit log.

### Environment variables

See `.env.example`:

- `GITHUB_TOKEN` — required for repo access
- `GROQ_API_KEY` — required for agents
- `LLM_MODEL`, `LLM_BASE_URL` — Groq config

## Changelog

- 2026-06-25 — Updated stack for GitHub repo auditing
- 2026-06-25 — Initial tech stack doc
