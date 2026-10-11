# local-target-github-repo

**Status:** active  
**Updated:** 2026-10-10  
**Related:** [local-safety-lab-scope.md](local-safety-lab-scope.md), [local-agent-recon.md](local-agent-recon.md), [local-target-vuln-sample.md](local-target-vuln-sample.md)

## Summary

GitHub repositories are SPECTRE's **primary v1 target**. Agents audit repos you own or have explicit permission to test — mapping surface area, hunting secrets and misconfigs, validating findings, and producing a repo security report.

## Context

Repo auditing is a natural fit for SPECTRE: the demo runs against real GitHub targets (your repos), findings are concrete (leaked keys, CVEs in `package-lock.json`), and the handoff story is compelling ("Recon mapped 12 workflows → VulnHunter found an exposed token → Exploiter confirmed it's live").

## Implementation

### Scope file format

```yaml
# scopes/example.yaml
name: my-app-audit
description: Authorized audit of my-app repository
allowed_repos:
  - tmestery/my-app
allowed_branches:
  - main
  - develop
# Optional: restrict to paths
include_paths:
  - "**"
exclude_paths:
  - "node_modules/**"
  - "dist/**"
max_commits_depth: 50        # how far back to scan history
max_duration_minutes: 30
authorization: owner-confirmed
```

### GitHub token requirements

| Scope | Purpose |
|-------|---------|
| `repo` (private) or `public_repo` | Clone, read contents, workflows |
| `read:org` | Org repos (if applicable) |

Store in `.env` as `GITHUB_TOKEN`. Never commit tokens.

### Demo repos (suggested)

| Repo | Purpose |
|------|---------|
| **Your own repo** | Primary demo — real, authorized |
| **`tmestery/SPECTRE`** | Dogfood — audit the project itself |
| **[`tmestery/spectre-vuln-sample`](https://github.com/tmestery/spectre-vuln-sample)** | Curated planted secrets / CVEs / unsafe workflow — see [local-target-vuln-sample.md](local-target-vuln-sample.md) |

### Demo audit path

| Step | Agent | Action | Expected finding |
|------|-------|--------|------------------|
| 1 | Recon | GitHub API + clone | Repo layout, languages, workflows, deps manifest |
| 2 | VulnHunter | gitleaks + osv-scanner | Secret in history or CVE in dependency |
| 3 | Exploiter | Validate secret / confirm CVE reachability | `validation_attempt` confirmed |
| 4 | Reporter | Synthesize | Markdown report with file links and remediation |

### CLI

```bash
python -m spectre.cli run \
  --repo tmestery/spectre-vuln-sample \
  --scope scopes/vuln-sample.yaml \
  --branch main
```

### What agents check (v1)

| Category | Examples |
|----------|----------|
| **Secrets** | API keys, tokens, private keys in code or git history |
| **Dependencies** | Known CVEs in npm, pip, Go modules |
| **Workflows** | Unsafe `pull_request_target`, unpinned actions, secret exfil patterns |
| **Config** | `.env` committed, overly permissive CORS, debug flags in prod configs |
| **Exposure** | Public repo with sensitive filenames, missing `.gitignore` patterns |

## Tests

| Case | Type |
|------|------|
| scope.yaml validates allowed repo slug | Positive |
| Out-of-repo slug rejected before clone | Negative |
| Excluded paths not scanned | Negative |
| Missing GITHUB_TOKEN raises clear error | Negative |

## Changelog

- 2026-10-10 — Linked vuln sample repo + `scopes/vuln-sample.yaml` (#13)
- 2026-06-25 — Initial GitHub repo target doc (primary v1 target)
