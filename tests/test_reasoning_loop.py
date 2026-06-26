import pytest

from spectre.agents.base import AgentContext
from spectre.agents.reasoning import AgentReasoningLoop, AgentTool
from spectre.agents.reasoning.prompts import REASONING_RESPONSE_SCHEMA
from spectre.bus.store import FindingsBus
from spectre.llm.client import MockLLMClient
from spectre.schemas.scope import RepoScope


@pytest.fixture
async def bus(tmp_path):
    store = FindingsBus(tmp_path / "eng_reason" / "events.db")
    await store.connect()
    yield store
    await store.close()


@pytest.fixture
def ctx(scope) -> AgentContext:
    return AgentContext(
        engagement_id="eng_reason",
        session_id="eng_reason",
        scope=scope,
        repo="tmestery/SPECTRE",
        branch="main",
        agent_id="recon",
        activation_id="act_reason",
        iteration=1,
        max_iterations=6,
    )


@pytest.fixture
def scope() -> RepoScope:
    return RepoScope(
        name="test-scope",
        allowed_repos=["tmestery/SPECTRE"],
        allowed_branches=["main"],
    )


@pytest.mark.asyncio
async def test_reasoning_loop_runs_tool_then_completes(ctx, bus):
    llm = MockLLMClient(
        queue=[
            '{"action":"tool","reasoning":"Mapping repository.","tool":"probe","params":{}}',
            '{"action":"complete","reasoning":"Done.","message":"Recon complete.","handoff_rationale":"Ready for vuln scan."}',
        ]
    )
    calls: list[str] = []

    async def probe(_: dict) -> dict:
        calls.append("probe")
        return {"files": 3}

    tools = {
        "probe": AgentTool(name="probe", description="probe", handler=probe),
    }
    loop = AgentReasoningLoop(llm, max_steps=4)
    result = await loop.run(
        ctx,
        bus,
        system_prompt="test",
        tools=tools,
        initial_context={"repo": "tmestery/SPECTRE"},
        response_schema=REASONING_RESPONSE_SCHEMA,
    )
    assert result.completed
    assert calls == ["probe"]
    assert len(result.steps) == 2


@pytest.mark.asyncio
async def test_reasoning_loop_skips_without_llm(ctx, bus):
    from spectre.llm.client import LLMClient

    llm = LLMClient(provider="groq", api_key="", model="x", base_url="http://example.com")
    loop = AgentReasoningLoop(llm)
    result = await loop.run(
        ctx,
        bus,
        system_prompt="test",
        tools={},
        initial_context={},
        response_schema=REASONING_RESPONSE_SCHEMA,
    )
    assert result.skipped


@pytest.mark.asyncio
async def test_reasoning_loop_rejects_unknown_tool(ctx, bus):
    llm = MockLLMClient(
        queue=[
            '{"action":"tool","reasoning":"Bad tool","tool":"missing","params":{}}',
            '{"action":"complete","reasoning":"Stop","message":"done"}',
        ]
    )
    loop = AgentReasoningLoop(llm, max_steps=3)
    result = await loop.run(
        ctx,
        bus,
        system_prompt="test",
        tools={},
        initial_context={},
        response_schema=REASONING_RESPONSE_SCHEMA,
    )
    assert result.steps[0].tool_result == {"error": "unknown tool: missing"}


@pytest.mark.asyncio
async def test_reasoning_loop_publishes_messages(ctx, bus):
    llm = MockLLMClient(
        queue=[
            '{"action":"message","reasoning":"Thinking","message":"Status update"}',
            '{"action":"complete","reasoning":"Done","message":"Finished"}',
        ]
    )
    loop = AgentReasoningLoop(llm, max_steps=3)
    await loop.run(
        ctx,
        bus,
        system_prompt="test",
        tools={},
        initial_context={},
        response_schema=REASONING_RESPONSE_SCHEMA,
    )
    events = await bus.all_events()
    messages = [e for e in events if e.type.value == "agent_message"]
    assert len(messages) >= 2
