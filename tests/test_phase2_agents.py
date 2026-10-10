import pytest

from spectre.agents.base import AgentContext
from spectre.agents.exploiter.agent import ExploiterAgent
from spectre.agents.vuln_hunter.agent import VulnHunterAgent
from spectre.bus.store import FindingsBus
from spectre.schemas.events import BusEvent
from spectre.schemas.finding import Finding, FindingType, Severity
from spectre.schemas.scope import RepoScope
from spectre.tools.github import GitHubClient


@pytest.fixture
async def bus(tmp_path):
    instance = FindingsBus(tmp_path / "eng_test" / "events.db")
    await instance.connect()
    yield instance
    await instance.close()


def _ctx(workspace: str) -> AgentContext:
    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    return AgentContext(
        engagement_id="eng_test",
        session_id="eng_test",
        scope=scope,
        repo="tmestery/SPECTRE",
        branch="main",
        agent_id="vuln_hunter",
        activation_id="act_1",
        iteration=1,
        max_iterations=1,
        workspace_path=workspace,
    )


@pytest.mark.asyncio
async def test_vuln_hunter_publishes_secret_finding(tmp_path, bus, monkeypatch):
    monkeypatch.setattr("spectre.tools.gitleaks.shutil.which", lambda _: None)
    workspace = tmp_path / "repo"
    workspace.mkdir()
    (workspace / "leak.txt").write_text("AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
    await bus.publish(
        BusEvent.finding_event(
            "eng_test",
            Finding(type=FindingType.REPOSITORY, agent="recon", target="tmestery/SPECTRE", title="repo"),
        )
    )

    agent = VulnHunterAgent()
    result = await agent.run(_ctx(str(workspace)), bus)

    assert result.status.value == "complete"
    findings = await bus.query_findings(finding_type="secret")
    assert len(findings) >= 1


@pytest.mark.asyncio
async def test_vuln_hunter_without_workspace_exhausts(bus):
    agent = VulnHunterAgent()
    result = await agent.run(_ctx(""), bus)
    assert result.status.value == "exhausted"


@pytest.mark.asyncio
async def test_exploiter_validates_secret(tmp_path, bus):
    secret = Finding(
        type=FindingType.SECRET,
        agent="vuln_hunter",
        target="tmestery/SPECTRE:leak.txt",
        title="secret",
        severity=Severity.HIGH,
        confidence=0.9,
        evidence={"rule": "aws-access-key", "snippet_redacted": "AKIA****"},
    )
    await bus.publish(BusEvent.finding_event("eng_test", secret))

    agent = ExploiterAgent()
    ctx = _ctx(str(tmp_path))
    ctx.agent_id = "exploiter"
    result = await agent.run(ctx, bus)

    assert result.status.value == "complete"
    validations = await bus.query_findings(finding_type="validation_attempt")
    assert len(validations) == 1
    assert validations[0].status.value == "confirmed"


@pytest.mark.asyncio
async def test_exploiter_marks_invalid_secret_false_positive(bus):
    secret = Finding(
        type=FindingType.SECRET,
        agent="vuln_hunter",
        target="tmestery/SPECTRE:x",
        title="secret",
        evidence={"rule": "unknown", "snippet_redacted": "not-a-key"},
    )
    await bus.publish(BusEvent.finding_event("eng_test", secret))

    agent = ExploiterAgent()
    ctx = _ctx("")
    ctx.agent_id = "exploiter"
    await agent.run(ctx, bus)

    validations = await bus.query_findings(finding_type="validation_attempt")
    assert validations[0].status.value == "false_positive"


@pytest.mark.asyncio
async def test_exploiter_no_findings_exhausts(bus):
    agent = ExploiterAgent()
    ctx = _ctx("")
    ctx.agent_id = "exploiter"
    result = await agent.run(ctx, bus)
    assert result.status.value == "exhausted"


@pytest.mark.asyncio
async def test_vuln_hunter_bootstraps_workspace_when_missing(tmp_path, bus, monkeypatch):
    workspace = tmp_path / "clone"
    workspace.mkdir()

    async def fake_inventory(self, repo, branch):
        from spectre.tools.github import RepoInventory

        return RepoInventory(
            repo=repo,
            branch=branch,
            default_branch=branch,
            clone_path=workspace,
        )

    monkeypatch.setattr(
        GitHubClient,
        "inventory_repo",
        fake_inventory,
    )

    class FakeEngagement:
        workspace_path = None

    engagement = FakeEngagement()
    agent = VulnHunterAgent()
    result = await agent.run(_ctx(""), bus, engagement=engagement)

    assert result.status.value == "complete"
    assert engagement.workspace_path == str(workspace)
