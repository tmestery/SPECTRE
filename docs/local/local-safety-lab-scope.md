# local-safety-lab-scope

**Status:** active  
**Updated:** 2026-06-25  
**Related:** [local-target-github-repo.md](local-target-github-repo.md), `spectre/safety/` (planned)

## Summary

SPECTRE audits **authorized GitHub repositories only**. Repo scope enforcement, token redaction, audit logging, and kill switches prevent drive-by scanning or credential leakage through findings.

## Context

Automated secret scanning and validation is high-risk if misused. Safety is architectural — every clone and API call passes through scope checks; violations halt the engagement.

## Implementation

### Scope file format

```yaml
# scopes/my-app.yaml
name: my-app-audit
description: Authorized audit of my-app repository
allowed_repos:
  - tmestery/my-app
allowed_branches:
  - main
include_paths:
  - "**"
exclude_paths:
  - "node_modules/**"
  - "dist/**"
max_commits_depth: 50
max_duration_minutes: 30
authorization: owner-confirmed
```

### Enforcement points

| Layer | Check |
|-------|-------|
| CLI | Refuse `spectre run` without valid scope file and `GITHUB_TOKEN` |
| Orchestrator | Validate repo slug ∈ `allowed_repos` before clone |
| Tool wrapper | `safety.scope.check_repo(owner/repo)` before API/scan |
| Agent prompt | Include allowlist; refuse out-of-scope repos |
| UI | Display scope banner with repo slug and branch |

### Token and secret hygiene

- `GITHUB_TOKEN` in `.env` only — never commit
- Findings store **redacted** snippets (`AKIA****`, not full keys)
- Exploiter validation uses read-only checks where possible
- Audit log never records full tokens or response bodies with secrets

### Audit log

```json
{
  "type": "tool_invocation",
  "tool": "gitleaks",
  "target": "tmestery/my-app",
  "scope_check": "passed",
  "branch": "main",
  "exit_code": 0,
  "duration_ms": 8200,
  "timestamp": "..."
}
```

### Prohibited (hard rules)

- Scanning repos not in `allowed_repos`
- Org-wide sweeps without explicit per-repo authorization
- Committing `.env` with tokens
- Publishing full secrets to bus, UI, or reports
- Disabling scope checks outside test mocks

## Tests

| Case | Type |
|------|------|
| In-scope repo passes check | Positive |
| Out-of-scope repo slug rejected | Negative |
| Excluded paths skipped | Negative |
| Finding evidence redacts secret value | Negative |
| Missing scope file aborts engagement | Negative |

## Changelog

- 2026-06-25 — Rewrote for GitHub repo scope (replaces host/IP allowlist as primary)
- 2026-06-25 — Initial safety doc
