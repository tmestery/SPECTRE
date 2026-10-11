import pytest

from spectre.agents.base import AgentContext
from spectre.agents.report_judge.agent import ReportJudgeAgent
from spectre.agents.routing.registry import CognitiveRuntime
from spectre.bus.store import FindingsBus
from spectre.llm.client import LLMClient
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import Finding, FindingType
from spectre.schemas.scope import RepoScope


@pytest.fixture
async def bus(tmp_path):
    store = FindingsBus(tmp_path / "eng_rj" / "events.db")
    await store.connect()
    yield store
    await store.close()


def _ctx(repo: str = "tmestery/SPECTRE") -> AgentContext:
    return AgentContext(
        engagement_id="eng_rj",
        session_id="eng_rj",
        scope=RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"]),
        repo=repo,
        branch="main",
        agent_id="report_judge",
        activation_id="act_1",
        iteration=1,
        max_iterations=3,
    )


def _offline() -> CognitiveRuntime:
    return CognitiveRuntime.create(
        LLMClient(provider="groq", api_key="", model="x", base_url="http://x")
    )


@pytest.mark.asyncio
async def test_report_judge_accepts_backed_report(bus):
    await bus.publish(
        BusEvent.finding_event(
            "eng_rj",
            Finding(
                type=FindingType.VULNERABILITY,
                agent="vuln_hunter",
                target="tmestery/SPECTRE:pkg",
                title="cve",
                evidence={"cve_id": "CVE-2024-1234", "path": "package.json"},
            ),
        )
    )
    await bus.publish(
        BusEvent(
            type=EventType.REPORT_SECTION,
            session_id="eng_rj",
            payload={
                "section_id": "exec",
                "title": "Executive",
                "markdown": "Found `CVE-2024-1234` in `package.json`.",
            },
        )
    )
    result = await ReportJudgeAgent(_offline()).run(_ctx(), bus)
    assert result.status.value == "complete"
    events = await bus.all_events(types=[EventType.REPORT_VERDICT])
    assert events[0].payload["verdict"] == "accept"


@pytest.mark.asyncio
async def test_report_judge_revises_invented_cve(bus):
    await bus.publish(
        BusEvent(
            type=EventType.REPORT_SECTION,
            session_id="eng_rj",
            payload={
                "section_id": "exec",
                "title": "Executive",
                "markdown": "Critical `CVE-2099-99999` in production.",
            },
        )
    )
    result = await ReportJudgeAgent(_offline()).run(_ctx(), bus)
    assert result.status.value == "complete"
    events = await bus.all_events(types=[EventType.REPORT_VERDICT])
    assert events[0].payload["verdict"] == "revise"
    assert events[0].payload["issues"]


@pytest.mark.asyncio
async def test_report_judge_blocks_out_of_scope(bus):
    result = await ReportJudgeAgent(_offline()).run(_ctx("octocat/Hello-World"), bus)
    assert result.status.value == "blocked"


@pytest.mark.asyncio
async def test_report_judge_exhausts_without_sections(bus):
    result = await ReportJudgeAgent(_offline()).run(_ctx(), bus)
    assert result.status.value == "exhausted"
