import pytest
from pathlib import Path

from spectre.tools.gitleaks import GitleaksScanner
from spectre.tools.workflows import WorkflowAnalyzer


@pytest.fixture
async def bus(tmp_path):
    from spectre.bus.store import FindingsBus

    instance = FindingsBus(tmp_path / "s" / "events.db")
    await instance.connect()
    yield instance
    await instance.close()


@pytest.mark.asyncio
async def test_fallback_secret_scan_finds_pattern(tmp_path, bus):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    (workspace / "config.env").write_text('API_KEY="supersecretvalue123"\n', encoding="utf-8")

    scanner = GitleaksScanner(bus, "session")
    matches = await scanner.scan(workspace, "tmestery/SPECTRE")

    assert len(matches) >= 1
    assert matches[0].rule == "generic-api-key"


@pytest.mark.asyncio
async def test_empty_workspace_returns_no_matches(tmp_path, bus):
    workspace = tmp_path / "empty"
    workspace.mkdir()

    scanner = GitleaksScanner(bus, "session")
    matches = await scanner.scan(workspace, "tmestery/SPECTRE")
    assert matches == []


def test_workflow_analyzer_detects_pull_request_target(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    workflow = workspace / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("on:\n  pull_request_target:\n    types: [opened]\n", encoding="utf-8")

    issues = WorkflowAnalyzer().analyze_paths(workspace, [".github/workflows/ci.yml"])
    assert any(issue.pattern == "pull_request_target" for issue in issues)


def test_workflow_analyzer_missing_file():
    issues = WorkflowAnalyzer().analyze_paths(Path("/nonexistent"), ["missing.yml"])
    assert issues == []
