# local-dev-github-templates

**Status:** active  
**Updated:** 2026-10-10  
**Related:** [local-dev-git-workflow.md](local-dev-git-workflow.md), `.github/`, issue #51

## Summary

Contributor templates and CI live under `.github/`. Pull requests use `PULL_REQUEST_TEMPLATE/`; issues use YAML forms in `ISSUE_TEMPLATE/`.

## Context

SPECTRE requires issue-first work and PRs with a summary, test plan, and safety notes. Templates encode that checklist so agents and humans do not invent ad-hoc PR bodies.

## Implementation

```
.github/
  PULL_REQUEST_TEMPLATE/
    pull_request_template.md   # default PR body
    docs.md                    # docs-only PRs (?template=docs.md)
  ISSUE_TEMPLATE/
    config.yml                 # blank issues + doc links
    bug_report.yml
    feature_request.yml
    chore.yml
  workflows/
    ci.yml                     # ruff, pytest, mypy (advisory), vitest, UI build
```

### PR templates

- Default: `.github/PULL_REQUEST_TEMPLATE/pull_request_template.md`
- Docs-only: append `?template=docs.md` on the compare URL (see [GitHub query parameters](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/using-query-parameters-to-create-a-pull-request))

### Issue forms

YAML issue forms replace legacy markdown templates. `config.yml` keeps blank issues enabled and links `AGENTS.md` plus the local docs index.

### CI

Workflow sets `permissions: contents: read` and a concurrency group that cancels in-progress runs on the same ref. Job set is unchanged: Python lint/test, gradual mypy, UI test/build.

### Placeholder dirs

- Remove `.gitkeep` when the directory already has tracked files (e.g. `scopes/`).
- Keep `.gitkeep` under `reports/` and `data/sessions/` — those trees are gitignored except for the keep file.

## Tests

`tests/test_github_templates.py` — layout and form guardrails (existence, legacy paths gone, CI least-privilege keys, required summary fields, `.gitkeep` policy).

## Changelog

- 2026-10-10 — Moved PR templates into `PULL_REQUEST_TEMPLATE/`; YAML issue forms; CI permissions/concurrency; drop redundant `scopes/.gitkeep` (#51)
