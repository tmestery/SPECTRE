import pytest

from spectre.agents.base import AgentContext
from spectre.agents.handoff_judge.agent import HandoffJudgeAgent
from spectre.agents.routing.registry import CognitiveRuntime
from spectre.bus.store import FindingsBus
from spectre.llm.client import LLMClient
from spectre.orchestrator.registry import AgentRegistry
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.judging import handoff_verdict_event
from spectre.schemas.scope import RepoScope


@pytest.fixture
async def bus(tmp_path):
    store = FindingsBus(tmp_path / "eng_hj" / "events.db")
    await store.connect()
    yield store
    await store.close()


def _ctx(repo: str = "tmestery/SPECTRE") -> AgentContext:
    return AgentContext(
        engagement_id="eng_hj",
        session_id="eng_hj",
        scope=RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"]),
        repo=repo,
        branch="main",
        agent_id="handoff_judge",
        activation_id="act_1",
        iteration=1,
        max_iterations=3,
    )


def _offline() -> CognitiveRuntime:
    return CognitiveRuntime.create(
        LLMClient(provider="groq", api_key="", model="x", base_url="http://x")
    )


@pytest.mark.asyncio
async def test_handoff_judge_approves_repo_mapped(bus):
    await bus.publish(
        BusEvent(
            type=EventType.HANDOFF_DECISION,
            session_id="eng_hj",
            payload={
                "rule": "repo_mapped",
                "from_agent": "recon",
                "to_agent": "vuln_hunter",
                "rationale": "mapped",
            },
        )
    )
    result = await HandoffJudgeAgent(_offline()).run(_ctx(), bus)
    assert result.status.value == "complete"
    events = await bus.all_events(types=[EventType.HANDOFF_VERDICT])
    assert len(events) == 1
    assert events[0].payload["verdict"] == "approve"
    assert events[0].payload["advisory"] is True


@pytest.mark.asyncio
async def test_handoff_judge_blocks_out_of_scope(bus):
    result = await HandoffJudgeAgent(_offline()).run(_ctx("octocat/Hello-World"), bus)
    assert result.status.value == "blocked"


@pytest.mark.asyncio
async def test_handoff_judge_exhausts_without_decisions(bus):
    result = await HandoffJudgeAgent(_offline()).run(_ctx(), bus)
    assert result.status.value == "exhausted"


@pytest.mark.asyncio
async def test_handoff_judge_skips_already_verdicted(bus):
    decision = BusEvent(
        type=EventType.HANDOFF_DECISION,
        session_id="eng_hj",
        payload={"rule": "repo_mapped", "from_agent": "recon", "to_agent": "vuln_hunter"},
    )
    await bus.publish(decision)
    await bus.publish(
        handoff_verdict_event(
            "eng_hj",
            {
                "decision_id": decision.id,
                "verdict": "approve",
                "rationale": "done",
                "advisory": True,
            },
        )
    )
    result = await HandoffJudgeAgent(_offline()).run(_ctx(), bus)
    assert result.status.value == "exhausted"
    assert len(await bus.all_events(types=[EventType.HANDOFF_VERDICT])) == 1


def test_handoff_judge_registered():
    registry = AgentRegistry(
        llm=LLMClient(provider="groq", api_key="", model="x", base_url="http://x")
    )
    assert registry.get("handoff_judge").id == "handoff_judge"
