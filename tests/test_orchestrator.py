from pathlib import Path

import pytest

from spectre.agents.base import AgentContext, AgentResult, AgentResultStatus
from spectre.bus.store import FindingsBus
from spectre.orchestrator.loop import Orchestrator, create_engagement
from spectre.schemas.events import BusEvent
from spectre.schemas.finding import Finding, FindingType
from spectre.schemas.scope import RepoScope


class FakeRecon:
    id = "recon"
    max_iterations = 1

    def __init__(self, workspace: Path | None = None) -> None:
        self.workspace = workspace

    async def run(self, ctx: AgentContext, bus: FindingsBus, engagement=None, **deps) -> AgentResult:
        if self.workspace and engagement is not None:
            (self.workspace / "leak.txt").write_text("AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
            workflow_dir = self.workspace / ".github" / "workflows"
            workflow_dir.mkdir(parents=True, exist_ok=True)
            (workflow_dir / "ci.yml").write_text(
                "on:\n  pull_request_target:\n    types: [opened]\n",
                encoding="utf-8",
            )
            engagement.workspace_path = str(self.workspace)
        await bus.publish(
            BusEvent.finding_event(
                ctx.session_id,
                Finding(
                    type=FindingType.REPOSITORY,
                    agent="recon",
                    target=ctx.repo,
                    title="repo",
                ),
            )
        )
        await bus.publish(
            BusEvent.finding_event(
                ctx.session_id,
                Finding(
                    type=FindingType.FILE,
                    agent="recon",
                    target=f"{ctx.repo}:README.md",
                    title="file",
                ),
            )
        )
        if self.workspace:
            await bus.publish(
                BusEvent.finding_event(
                    ctx.session_id,
                    Finding(
                        type=FindingType.WORKFLOW,
                        agent="recon",
                        target=f"{ctx.repo}:.github/workflows/ci.yml",
                        title="workflow",
                        evidence={"path": ".github/workflows/ci.yml"},
                    ),
                )
            )
        return AgentResult(status=AgentResultStatus.COMPLETE)


@pytest.mark.asyncio
async def test_orchestrator_runs_recon_to_reporter_chain(tmp_path, monkeypatch):
    monkeypatch.setattr("spectre.tools.gitleaks.shutil.which", lambda _: None)

    async def _no_github(*_args, **_kwargs):
        raise AssertionError("GitHubClient must not be called in offline orchestrator tests")

    monkeypatch.setattr("spectre.tools.github.GitHubClient.inventory_repo", _no_github)

    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    engagement = create_engagement("tmestery/SPECTRE", "main", scope)
    bus = FindingsBus(tmp_path / engagement.id / "events.db")
    await bus.connect()

    workspace = tmp_path / "clone"
    workspace.mkdir()

    orchestrator = Orchestrator(bus)
    orchestrator.registry._agents["recon"] = FakeRecon(workspace)

    result = await orchestrator.run(engagement)
    findings = await bus.all_findings()

    assert result.status.value == "complete"
    assert len(findings) >= 2
    await bus.close()


@pytest.mark.asyncio
async def test_orchestrator_runs_phase2_chain_with_validation(tmp_path, monkeypatch):
    monkeypatch.setattr("spectre.tools.gitleaks.shutil.which", lambda _: None)

    async def _no_github(*_args, **_kwargs):
        raise AssertionError("GitHubClient must not be called in offline orchestrator tests")

    monkeypatch.setattr("spectre.tools.github.GitHubClient.inventory_repo", _no_github)

    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    engagement = create_engagement("tmestery/SPECTRE", "main", scope)
    bus = FindingsBus(tmp_path / engagement.id / "events.db")
    await bus.connect()

    workspace = tmp_path / "clone"
    workspace.mkdir()

    orchestrator = Orchestrator(bus)
    orchestrator.registry._agents["recon"] = FakeRecon(workspace)

    result = await orchestrator.run(engagement)
    findings = await bus.all_findings()

    assert result.status.value == "complete"
    assert any(f.type.value == "secret" for f in findings)
    assert any(f.type.value == "validation_attempt" for f in findings)
    assert any(f.type.value == "misconfiguration" for f in findings)
    await bus.close()


@pytest.mark.asyncio
async def test_orchestrator_rejects_out_of_scope_repo(tmp_path):
    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    engagement = create_engagement("octocat/Hello-World", "main", scope)
    bus = FindingsBus(tmp_path / engagement.id / "events.db")
    await bus.connect()
    orchestrator = Orchestrator(bus)

    with pytest.raises(Exception):
        await orchestrator.run(engagement)

    await bus.close()
