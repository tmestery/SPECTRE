---
name: git-workflow
description: >-
  Enforces SPECTRE Git and GitHub workflow: issue first, branch, small commits,
  PR with description and test plan, no direct commits to main. Use before
  starting any change or when creating branches, commits, or pull requests.
---

# Git Workflow

**No code changes without an issue and a PR.** Do not commit directly to `main`.

## Workflow

1. **Issue first** — Open a GitHub issue. Reference in branch and PR (`#123`).
2. **Branch** — From latest `main`:
   - `feature/<issue>-<short-slug>`
   - `fix/<issue>-<short-slug>`
   - `chore/<issue>-<short-slug>`
   - `research/<issue>-<short-slug>`
3. **Work** — Small focused commits.
4. **Verify** — Tests and build green (per **development-standards**).
5. **PR** — Against `main` with summary, test plan, `Closes #<issue>`.
6. **Review** — Address feedback; keep scope tight.
7. **Merge** — After approval and CI green.

## Commit messages

- Imperative mood: `Add recon agent nmap wrapper`
- Reference issue: `Implement findings bus (#2)`

## Git habits

- Pull `main` before branching and before PR
- Never force-push `main`
- No secrets, `.env`, session data, or generated artifacts
- Stage only related files

## PR checklist

- [ ] Linked issue exists
- [ ] Branch up to date with `main`
- [ ] Tests pass (1 positive + 3 negative for new features)
- [ ] `docs/local/` updated if behavior or architecture changed
- [ ] Scope/safety impact noted for offensive tooling changes
- [ ] PR description includes summary and test plan
