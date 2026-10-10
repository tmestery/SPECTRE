import pytest

from spectre.bus.store import FindingsBus
from spectre.report.generator import ReportGenerator
from spectre.schemas.events import BusEvent
from spectre.schemas.finding import Finding, FindingStatus, FindingType, Severity
from spectre.schemas.scope import RepoScope


@pytest.fixture
def scope() -> RepoScope:
    return RepoScope(name="test", allowed_repos=["tmestery/SPECTRE"])


@pytest.fixture
async def bus(tmp_path):
    instance = FindingsBus(tmp_path / "eng_test" / "events.db")
    await instance.connect()
    yield instance
    await instance.close()


def _secret_finding() -> Finding:
    return Finding(
        type=FindingType.SECRET,
        agent="vuln_hunter",
        target="tmestery/SPECTRE:src/config.ts",
        severity=Severity.HIGH,
        title="AWS key",
        evidence={
            "file": "src/config.ts",
            "line": 14,
            "snippet_redacted": "AKIA****",
        },
        status=FindingStatus.TENTATIVE,
    )


def test_report_includes_github_permalink(scope):
    generator = ReportGenerator("tmestery/SPECTRE", "main", scope)
    md = generator.render_markdown([_secret_finding()], [])
    assert "https://github.com/tmestery/SPECTRE/blob/main/src/config.ts#L14" in md
    assert "AKIA****" in md


def test_empty_findings_produces_clean_report(scope):
    generator = ReportGenerator("tmestery/SPECTRE", "main", scope)
    md = generator.render_markdown([], [])
    assert "No security findings" in md
    assert "# SPECTRE Repository Security Report" in md


def test_secrets_redacted_in_report(scope):
    generator = ReportGenerator("tmestery/SPECTRE", "main", scope)
    raw = Finding(
        type=FindingType.SECRET,
        agent="vuln_hunter",
        target="tmestery/SPECTRE:leak.env",
        severity=Severity.HIGH,
        title="token",
        evidence={"snippet_redacted": "ghp_****", "file": "leak.env"},
    )
    md = generator.render_markdown([raw], [])
    assert "ghp_****" in md
    assert "ghp_" not in md.replace("ghp_****", "")


def test_duplicate_findings_deduped(scope):
    generator = ReportGenerator("tmestery/SPECTRE", "main", scope)
    dup_a = _secret_finding()
    dup_b = _secret_finding()
    md = generator.render_markdown([dup_a, dup_b], [])
    assert md.count(dup_a.id) == 1 or md.count("AWS key") == 1


@pytest.mark.asyncio
async def test_export_report_missing_session(tmp_path):
    from spectre.cli import _export_report
    import argparse

    args = argparse.Namespace(session="eng_missing", format="markdown", output=None)
    code = await _export_report(args)
    assert code == 1


@pytest.mark.asyncio
async def test_reporter_writes_report_files(tmp_path, bus, scope, monkeypatch):
    from spectre.agents.base import AgentContext
    from spectre.agents.reporter.agent import ReporterAgent

    monkeypatch.chdir(tmp_path)

    await bus.publish(
        BusEvent.finding_event("eng_test", _secret_finding()),
    )
    ctx = AgentContext(
        engagement_id="eng_test",
        session_id="eng_test",
        scope=scope,
        repo="tmestery/SPECTRE",
        branch="main",
        agent_id="reporter",
        activation_id="act_1",
        iteration=1,
        max_iterations=1,
    )
    agent = ReporterAgent()
    result = await agent.run(ctx, bus)
    assert result.status.value == "complete"
    assert (tmp_path / "reports" / "eng_test.md").exists()
    assert (tmp_path / "reports" / "eng_test.html").exists()
