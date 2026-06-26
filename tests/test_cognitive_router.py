import pytest

from spectre.agents.base import AgentContext
from spectre.agents.routing.router import AgentCognitiveRouter
from spectre.bus.store import FindingsBus
from spectre.llm.client import MockLLMClient
from spectre.schemas.scope import RepoScope


@pytest.fixture
async def bus(tmp_path):
    store = FindingsBus(tmp_path / "eng_test" / "events.db")
    await store.connect()
    yield store
    await store.close()


@pytest.fixture
def scope() -> RepoScope:
    return RepoScope(
        name="test-scope",
        allowed_repos=["tmestery/SPECTRE"],
        allowed_branches=["main"],
    )


@pytest.fixture
def ctx(scope) -> AgentContext:
    return AgentContext(
        engagement_id="eng_test",
        session_id="eng_test",
        scope=scope,
        repo="tmestery/SPECTRE",
        branch="main",
        agent_id="recon",
        activation_id="act_test",
        iteration=1,
        max_iterations=1,
    )


@pytest.mark.asyncio
async def test_cognitive_router_runs_recon_subagent(tmp_path, ctx, bus):
    llm = MockLLMClient()
    router = AgentCognitiveRouter(llm)
    results = await router.run_pipeline(
        "recon",
        ctx,
        bus,
        {"inventory": {"repo": "tmestery/SPECTRE", "file_count": 3, "workflows": [], "dependencies": []}},
    )
    assert len(results) == 1
    assert results[0].subagent_id == "surface_analyst"
    assert results[0].findings


@pytest.mark.asyncio
async def test_cognitive_router_skips_when_llm_unavailable(tmp_path, ctx, bus, capsys):
    from spectre.llm.client import LLMClient

    llm = LLMClient(provider="groq", api_key="", model="test", base_url="http://example.com")
    router = AgentCognitiveRouter(llm)
    results = await router.run_pipeline("recon", ctx, bus, {"inventory": {}})
    assert results == []


@pytest.mark.asyncio
async def test_cognitive_router_vuln_hunter_pipeline(tmp_path, ctx, bus):
    ctx.agent_id = "vuln_hunter"
    llm = MockLLMClient()
    router = AgentCognitiveRouter(llm)
    results = await router.run_pipeline(
        "vuln_hunter",
        ctx,
        bus,
        {
            "secret_findings": [{"title": "secret", "type": "secret"}],
            "vulnerability_findings": [],
            "misconfiguration_findings": [],
        },
    )
    assert len(results) == 3


@pytest.mark.asyncio
async def test_cognitive_router_unknown_subagent_not_in_pipeline(tmp_path, ctx, bus):
    llm = MockLLMClient()
    router = AgentCognitiveRouter(llm)
    results = await router.run_pipeline("reporter", ctx, bus, {"severity_counts": {}, "top_findings": []})
    assert len(results) == 1
    assert results[0].subagent_id == "executive_writer"
