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

    async def run(self, ctx: AgentContext, bus: FindingsBus, **deps) -> AgentResult:
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
        return AgentResult(status=AgentResultStatus.COMPLETE)


@pytest.mark.asyncio
async def test_orchestrator_runs_recon_to_reporter_chain(tmp_path):
    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    engagement = create_engagement("tmestery/SPECTRE", "main", scope)
    bus = FindingsBus(tmp_path / engagement.id / "events.db")
    await bus.connect()

    orchestrator = Orchestrator(bus)
    orchestrator.registry._agents["recon"] = FakeRecon()

    result = await orchestrator.run(engagement)
    findings = await bus.all_findings()

    assert result.status.value == "complete"
    assert len(findings) >= 2
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
