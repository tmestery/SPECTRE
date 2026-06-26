---
name: run-engagement
description: >-
  Runs a full SPECTRE GitHub repository audit. Use when demoing, testing the
  crew end-to-end, or validating handoffs against an authorized repo.
---

# Run Engagement

**Authorized repos only.** Verify scope before running.

## Prerequisites

- Scope file in `scopes/<name>.yaml`
- `GITHUB_TOKEN` and `GROQ_API_KEY` in `.env`
- Python env installed (once scaffold exists)

## Steps

1. **Create or verify scope**
   ```bash
   # scopes/spectre.yaml — allowed_repos: [tmestery/SPECTRE]
   ```

2. **Run audit**
   ```bash
   python -m spectre.cli run \
     --repo tmestery/SPECTRE \
     --scope scopes/spectre.yaml \
     --branch main
   ```

3. **Start demo UI** (Phase 3)
   ```bash
   npm run dev
   ```

4. **Watch** — agent chat, timeline with file links, handoffs

5. **Halt** if needed
   ```bash
   python -m spectre.cli halt --session <id>
   ```

6. **Export report**
   ```bash
   python -m spectre.cli report --session <id> --format markdown
   ```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Scope rejection | Repo slug must match `allowed_repos` exactly |
| 401 from GitHub | Check `GITHUB_TOKEN` scopes |
| Empty findings | Repo may be clean — use sample repo for demo |
| LLM errors | Verify `GROQ_API_KEY` |

## Checklist

- [ ] Only in-scope repos
- [ ] Engagement halted when done
- [ ] Report exported
- [ ] No tokens in committed artifacts
