import pytest

from spectre.agents.base import AgentContext
from spectre.agents.finding_judge.agent import FindingJudgeAgent
from spectre.agents.routing.registry import CognitiveRuntime
from spectre.bus.store import FindingsBus
from spectre.llm.client import LLMClient
from spectre.orchestrator.registry import AgentRegistry
from spectre.schemas.events import BusEvent
from spectre.schemas.finding import Finding, FindingType, Severity
from spectre.schemas.judging import JudgmentVerdict, make_judgment_finding
from spectre.schemas.scope import RepoScope


@pytest.fixture
async def bus(tmp_path):
    store = FindingsBus(tmp_path / "eng_judge" / "events.db")
    await store.connect()
    yield store
    await store.close()


def _ctx(repo: str = "tmestery/SPECTRE") -> AgentContext:
    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    return AgentContext(
        engagement_id="eng_judge",
        session_id="eng_judge",
        scope=scope,
        repo=repo,
        branch="main",
        agent_id="finding_judge",
        activation_id="act_1",
        iteration=1,
        max_iterations=3,
    )


def _offline_cognitive() -> CognitiveRuntime:
    llm = LLMClient(provider="groq", api_key="", model="x", base_url="http://example.com")
    return CognitiveRuntime.create(llm)


@pytest.mark.asyncio
async def test_finding_judge_upholds_high_confidence_secret(bus):
    await bus.publish(
        BusEvent.finding_event(
            "eng_judge",
            Finding(
                type=FindingType.SECRET,
                agent="vuln_hunter",
                target="tmestery/SPECTRE:leak.txt",
                title="AWS key",
                confidence=0.95,
                severity=Severity.HIGH,
                evidence={"snippet_redacted": "AKIA****"},
            ),
        )
    )
    agent = FindingJudgeAgent(_offline_cognitive())
    result = await agent.run(_ctx(), bus)
    assert result.status.value == "complete"
    judgments = await bus.query_findings(finding_type="judgment")
    assert len(judgments) == 1
    assert judgments[0].evidence["verdict"] == JudgmentVerdict.UPHOLD.value


@pytest.mark.asyncio
async def test_finding_judge_blocks_out_of_scope_engagement(bus):
    agent = FindingJudgeAgent(_offline_cognitive())
    result = await agent.run(_ctx(repo="octocat/Hello-World"), bus)
    assert result.status.value == "blocked"
    judgments = await bus.query_findings(finding_type="judgment")
    assert judgments == []


@pytest.mark.asyncio
async def test_finding_judge_skips_out_of_scope_finding_target(bus):
    await bus.publish(
        BusEvent.finding_event(
            "eng_judge",
            Finding(
                type=FindingType.SECRET,
                agent="vuln_hunter",
                target="octocat/Hello-World:leak.txt",
                title="foreign secret",
                confidence=0.99,
            ),
        )
    )
    agent = FindingJudgeAgent(_offline_cognitive())
    result = await agent.run(_ctx(), bus)
    assert result.status.value == "exhausted"
    judgments = await bus.query_findings(finding_type="judgment")
    assert judgments == []


@pytest.mark.asyncio
async def test_finding_judge_does_not_duplicate_existing_judgment(bus):
    secret = Finding(
        type=FindingType.SECRET,
        agent="vuln_hunter",
        target="tmestery/SPECTRE:x",
        title="secret",
        confidence=0.9,
    )
    await bus.publish(BusEvent.finding_event("eng_judge", secret))
    await bus.publish(
        BusEvent.finding_event(
            "eng_judge",
            make_judgment_finding(
                agent="finding_judge",
                target=secret.target,
                reviewed_finding_id=secret.id,
                verdict=JudgmentVerdict.UPHOLD,
                rationale="already judged",
            ),
        )
    )
    agent = FindingJudgeAgent(_offline_cognitive())
    result = await agent.run(_ctx(), bus)
    assert result.status.value == "exhausted"
    judgments = await bus.query_findings(finding_type="judgment")
    assert len(judgments) == 1


@pytest.mark.asyncio
async def test_finding_judge_registered_in_orchestrator_registry():
    registry = AgentRegistry(llm=LLMClient(provider="groq", api_key="", model="x", base_url="http://x"))
    agent = registry.get("finding_judge")
    assert agent.id == "finding_judge"
