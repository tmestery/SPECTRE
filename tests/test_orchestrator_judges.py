
import pytest

from spectre.agents.base import AgentContext, AgentResult, AgentResultStatus
from spectre.bus.store import FindingsBus
from spectre.config import settings
from spectre.orchestrator.loop import Orchestrator, create_engagement
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import Finding, FindingStatus, FindingType
from spectre.schemas.scope import RepoScope


class FakeRecon:
    id = "recon"
    max_iterations = 1

    async def run(self, ctx: AgentContext, bus: FindingsBus, engagement=None, **deps) -> AgentResult:
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


class FakeVuln:
    id = "vuln_hunter"
    max_iterations = 1

    async def run(self, ctx: AgentContext, bus: FindingsBus, engagement=None, **deps) -> AgentResult:
        await bus.publish(
            BusEvent.finding_event(
                ctx.session_id,
                Finding(
                    type=FindingType.SECRET,
                    agent="vuln_hunter",
                    target=f"{ctx.repo}:leak.txt",
                    title="secret",
                    confidence=0.95,
                ),
            )
        )
        return AgentResult(status=AgentResultStatus.COMPLETE)


class FakeExploiter:
    id = "exploiter"
    max_iterations = 1

    async def run(self, ctx: AgentContext, bus: FindingsBus, engagement=None, **deps) -> AgentResult:
        await bus.publish(
            BusEvent.finding_event(
                ctx.session_id,
                Finding(
                    type=FindingType.VALIDATION_ATTEMPT,
                    agent="exploiter",
                    target=f"{ctx.repo}:leak.txt",
                    title="validated",
                    status=FindingStatus.CONFIRMED,
                ),
            )
        )
        return AgentResult(status=AgentResultStatus.COMPLETE)


class FakeReporter:
    id = "reporter"
    max_iterations = 1

    async def run(self, ctx: AgentContext, bus: FindingsBus, engagement=None, **deps) -> AgentResult:
        await bus.publish(
            BusEvent(
                type=EventType.REPORT_SECTION,
                session_id=ctx.session_id,
                payload={"section_id": "exec", "title": "Exec", "markdown": "ok"},
            )
        )
        return AgentResult(status=AgentResultStatus.COMPLETE)


def _wire_fakes(orchestrator: Orchestrator) -> None:
    orchestrator.registry._agents["recon"] = FakeRecon()
    orchestrator.registry._agents["vuln_hunter"] = FakeVuln()
    orchestrator.registry._agents["exploiter"] = FakeExploiter()
    orchestrator.registry._agents["reporter"] = FakeReporter()


@pytest.mark.asyncio
async def test_orchestrator_schedules_judges_without_changing_handoffs(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "judges_enabled", True)
    monkeypatch.setattr(settings, "spectre_data_dir", tmp_path / "sessions")
    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    engagement = create_engagement("tmestery/SPECTRE", "main", scope)
    bus = FindingsBus(tmp_path / engagement.id / "events.db")
    await bus.connect()
    orchestrator = Orchestrator(bus)
    _wire_fakes(orchestrator)

    result = await orchestrator.run(engagement)
    assert result.status.value == "complete"

    events = await bus.all_events()
    handoffs = [e for e in events if e.type == EventType.HANDOFF_DECISION]
    assert any(e.payload.get("to_agent") == "vuln_hunter" for e in handoffs)
    assert any(e.type == EventType.HANDOFF_VERDICT for e in events)
    judgments = await bus.query_findings(finding_type="judgment")
    assert judgments
    assert any(e.type == EventType.REPORT_VERDICT for e in events)
    await bus.close()


@pytest.mark.asyncio
async def test_orchestrator_skips_judges_when_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "judges_enabled", False)
    monkeypatch.setattr(settings, "spectre_data_dir", tmp_path / "sessions")
    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    engagement = create_engagement("tmestery/SPECTRE", "main", scope)
    bus = FindingsBus(tmp_path / engagement.id / "events.db")
    await bus.connect()
    orchestrator = Orchestrator(bus)
    _wire_fakes(orchestrator)

    await orchestrator.run(engagement)
    events = await bus.all_events()
    assert not any(e.type == EventType.HANDOFF_VERDICT for e in events)
    assert await bus.query_findings(finding_type="judgment") == []
    await bus.close()


@pytest.mark.asyncio
async def test_judge_failure_does_not_abort_engagement(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "judges_enabled", True)
    monkeypatch.setattr(settings, "spectre_data_dir", tmp_path / "sessions")

    class BoomJudge:
        id = "finding_judge"
        max_iterations = 1

        async def run(self, *args, **kwargs):
            raise RuntimeError("judge boom")

    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    engagement = create_engagement("tmestery/SPECTRE", "main", scope)
    bus = FindingsBus(tmp_path / engagement.id / "events.db")
    await bus.connect()
    orchestrator = Orchestrator(bus)
    _wire_fakes(orchestrator)
    orchestrator.registry._agents["finding_judge"] = BoomJudge()

    result = await orchestrator.run(engagement)
    assert result.status.value == "complete"
    await bus.close()


@pytest.mark.asyncio
async def test_handoff_destination_unchanged_after_judge(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "judges_enabled", True)
    monkeypatch.setattr(settings, "spectre_data_dir", tmp_path / "sessions")
    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    engagement = create_engagement("tmestery/SPECTRE", "main", scope)
    bus = FindingsBus(tmp_path / engagement.id / "events.db")
    await bus.connect()
    orchestrator = Orchestrator(bus)
    _wire_fakes(orchestrator)

    await orchestrator.run(engagement)
    handoffs = [
        e for e in await bus.all_events() if e.type == EventType.HANDOFF_DECISION
    ]
    # First crew handoff after recon must still be vuln_hunter
    recon_handoff = next(e for e in handoffs if e.payload.get("from_agent") == "recon")
    assert recon_handoff.payload.get("to_agent") == "vuln_hunter"
    await bus.close()
