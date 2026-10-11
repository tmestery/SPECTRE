# local-dev-release

**Status:** active  
**Updated:** 2026-10-11  
**Related:** [pyproject.toml](../../pyproject.toml), [spectre/__init__.py](../../spectre/__init__.py), [package.json](../../package.json), [README.md](../../README.md)

## Summary

How SPECTRE versions are kept in sync and how to cut a GitHub Release (`vMAJOR.MINOR.PATCH`).

## Context

Product version appears in both the Python package and the Vite UI package. Tags use a leading `v` (e.g. `v1.0.0`). Do not change versions under `tests/fixtures/vuln-sample/` — that is demo target metadata, not SPECTRE’s release.

## Implementation

### Version sources (must match)

| File | Field |
|------|-------|
| `pyproject.toml` | `project.version` |
| `spectre/__init__.py` | `__version__` |
| `package.json` | `version` |
| `package-lock.json` | root `version` and `packages[""].version` |

### Bump checklist

1. Update the four sources above to the same semver string.
2. Confirm: `python -c "from spectre import __version__; print(__version__)"`.
3. Merge or push the bump to `main`.
4. On `main`:

```bash
git tag -a vX.Y.Z -m "SPECTRE X.Y.Z"
git push origin vX.Y.Z
gh release create vX.Y.Z --title "SPECTRE X.Y.Z" --notes "Release notes…"
```

Tag naming: `vMAJOR.MINOR.PATCH` (annotated tags preferred).

## Tests

N/A — process doc. Verify version import and tag/release presence after each cut.

## Changelog

- 2026-10-11 — Initial release process for 1.0.0
