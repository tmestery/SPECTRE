# local-target-vuln-sample

**Status:** active  
**Updated:** 2026-10-10  
**Related:** [local-target-github-repo.md](local-target-github-repo.md), [local-safety-lab-scope.md](local-safety-lab-scope.md), issue #13

## Summary

[`tmestery/spectre-vuln-sample`](https://github.com/tmestery/spectre-vuln-sample) is an intentionally vulnerable GitHub repo for repeatable SPECTRE demos. All planted credentials are **fake and inert**.

## Planted findings

| Finding | Path | Tool |
|---------|------|------|
| Fake AWS access key (`AKIAIOSFODNN7EXAMPLE`) | `src/config.js` | gitleaks / fallback |
| Known lodash advisories (e.g. GHSA-35jh-r3h4-6jhm) | `package-lock.json` | osv-scanner |
| `pull_request_target` + untrusted checkout | `.github/workflows/pr-target.yml` | WorkflowAnalyzer |

## Scope

```bash
python -m spectre.cli run \
  --repo tmestery/spectre-vuln-sample \
  --scope scopes/vuln-sample.yaml \
  --branch main
```

`scopes/vuln-sample.yaml` allowlists **only** `tmestery/spectre-vuln-sample` on `main`.

## Safety

- No real API keys, PATs, or cloud credentials
- AWS example values from public documentation patterns
- Repo is public for demo convenience; still require an authorized scope file before scanning

## Tests

Fixture copies live under `tests/fixtures/vuln-sample/`. See `tests/test_vuln_sample.py`.

## Changelog

- 2026-10-10 — Created sample repo, scope, and fixtures (#13)
