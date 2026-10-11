"""Guardrails for .github contributor templates and CI layout."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
GITHUB = ROOT / ".github"


def test_pull_request_templates_live_under_directory() -> None:
    default = GITHUB / "PULL_REQUEST_TEMPLATE" / "pull_request_template.md"
    docs = GITHUB / "PULL_REQUEST_TEMPLATE" / "docs.md"
    assert default.is_file()
    assert docs.is_file()
    text = default.read_text(encoding="utf-8")
    assert "Closes #" in text
    assert "Safety / scope" in text


def test_legacy_root_pull_request_template_removed() -> None:
    assert not (GITHUB / "pull_request_template.md").exists()


def test_issue_templates_are_yaml_forms() -> None:
    for name in ("bug_report.yml", "feature_request.yml", "chore.yml", "config.yml"):
        path = GITHUB / "ISSUE_TEMPLATE" / name
        assert path.is_file(), f"missing {path}"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)


def test_legacy_markdown_issue_templates_removed() -> None:
    leftovers = list((GITHUB / "ISSUE_TEMPLATE").glob("*.md"))
    assert leftovers == []


def test_ci_workflow_has_least_privilege_defaults() -> None:
    path = GITHUB / "workflows" / "ci.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["permissions"] == {"contents": "read"}
    assert "concurrency" in data
    assert "python" in data["jobs"]
    assert "ui" in data["jobs"]


def test_scopes_gitkeep_removed_when_real_files_tracked() -> None:
    assert (ROOT / "scopes" / "spectre.yaml").is_file()
    assert not (ROOT / "scopes" / ".gitkeep").exists()


def test_ignored_runtime_dirs_keep_gitkeep() -> None:
    """reports/ and data/sessions/ contents are gitignored; keep files stay."""
    assert (ROOT / "reports" / ".gitkeep").is_file()
    assert (ROOT / "data" / "sessions" / ".gitkeep").is_file()


@pytest.mark.parametrize(
    "filename",
    ["bug_report.yml", "feature_request.yml", "chore.yml"],
)
def test_issue_forms_require_summary(filename: str) -> None:
    data = yaml.safe_load((GITHUB / "ISSUE_TEMPLATE" / filename).read_text(encoding="utf-8"))
    bodies = data.get("body") or []
    summary_fields = [
        item for item in bodies if isinstance(item, dict) and item.get("id") == "summary"
    ]
    assert summary_fields, f"{filename} missing summary field"
    assert summary_fields[0].get("validations", {}).get("required") is True
