# local-agent-recon

**Status:** draft  
**Updated:** 2026-06-25  
**Related:** [local-target-github-repo.md](local-target-github-repo.md), [local-arch-agent-crew.md](local-arch-agent-crew.md)

## Summary

The Recon agent maps an authorized GitHub repository — structure, languages, dependency manifests, CI workflows, and notable files — publishing findings that seed VulnHunter's scan targets.

## Context

Recon is the entry point for every repo audit. It must be fast, scope-aware, and produce structured inventory findings rather than raw directory dumps.

## Implementation

### Responsibilities

- Fetch repo metadata via GitHub API (description, default branch, languages)
- Clone repo to temp dir (shallow, branch-scoped)
- Walk tree respecting `include_paths` / `exclude_paths`
- Inventory dependency manifests (`package.json`, `requirements.txt`, `go.mod`, etc.)
- List `.github/workflows/*.yml`
- Publish `repository`, `file`, `workflow`, `dependency` findings

### Tools

| Tool | Purpose | Output → Finding |
|------|---------|------------------|
| GitHub API | Metadata, contents listing | `repository` |
| git clone | Local tree for analysis | `file` |
| manifest parser | Detect lockfiles and deps | `dependency` |
| workflow parser | List CI workflows | `workflow` |

### Demo path (tmestery/SPECTRE)

1. API fetch repo metadata → `repository` finding
2. Clone `main` → file tree
3. Detect `package.json`, `pyproject.toml` (when added), workflows in `.github/`
4. Publish findings with `handoff_hint: vuln_hunter`

### Agent message examples

> "Mapping tmestery/SPECTRE on branch main — 36 tracked files, 2 workflows detected."

> "Found dependency manifests and GitHub Actions workflows. Handing off to VulnHunter for secret and CVE scans."

### Handoff trigger

[R1 repo_mapped](local-arch-handoff-protocol.md) when structure findings exist.

## Tests

| Case | Type |
|------|------|
| Mock GitHub API → valid repository finding | Positive |
| Out-of-scope repo rejected before clone | Negative |
| exclude_paths skips node_modules | Negative |
| Empty repo handled gracefully | Negative |
| Recon refuses gitleaks/sqlmap tools | Negative |

## Changelog

- 2026-06-25 — Rewrote for GitHub repo reconnaissance
- 2026-06-25 — Initial Recon agent doc
