---
name: setup-repo-scope
description: >-
  Creates scope files for authorized GitHub repo audits. Use when adding a new
  target repository or preparing a demo engagement.
---

# Setup Repo Scope

## Steps

1. **Confirm authorization** — you own the repo or have written permission to audit it.

2. **Create scope file** at `scopes/<name>.yaml`:
   ```yaml
   name: my-app-audit
   allowed_repos:
     - owner/repo
   allowed_branches:
     - main
   exclude_paths:
     - "node_modules/**"
   max_commits_depth: 50
   max_duration_minutes: 30
   authorization: owner-confirmed
   ```

3. **Set tokens** in `.env`:
   - `GITHUB_TOKEN` — `repo` or `public_repo` scope
   - `GROQ_API_KEY` — for agent reasoning

4. **Verify** — orchestrator rejects slugs not in `allowed_repos`.

5. **Document** — update [local-target-github-repo.md](../../../docs/local/local-target-github-repo.md) if adding a demo repo.

## Checklist

- [ ] `allowed_repos` is minimal (not `*/*`)
- [ ] Branches and path filters set
- [ ] No tokens in scope file or commits
