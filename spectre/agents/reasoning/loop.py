import json
from typing import Any

from spectre.agents.base import AgentContext
from spectre.agents.reasoning.schemas import AgentAction, ReasoningResult, ReasoningStep
from spectre.agents.reasoning.toolkit import AgentTool
from spectre.bus.store import FindingsBus
from spectre.config import settings
from spectre.llm.audit import audit_llm
from spectre.llm.client import LLMClient
from spectre.llm.prompts import SPECTRE_SYSTEM
from spectre.llm.types import LLMMessage
from spectre.schemas.events import BusEvent


class AgentReasoningLoop:
    def __init__(self, llm: LLMClient, max_steps: int | None = None) -> None:
        self.llm = llm
        self.max_steps = max_steps or settings.agent_reasoning_max_steps

    async def run(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        *,
        system_prompt: str,
        tools: dict[str, AgentTool],
        initial_context: dict[str, Any],
        response_schema: str,
    ) -> ReasoningResult:
        if not self.llm.available:
            return ReasoningResult(skipped=True)

        tool_catalog = [tool.schema() for tool in tools.values()]
        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=f"{SPECTRE_SYSTEM}\n{system_prompt}\n{response_schema}"),
            LLMMessage(
                role="user",
                content=(
                    f"Agent: {ctx.agent_id}\n"
                    f"Target: {ctx.repo} @ {ctx.branch}\n"
                    f"Scope: {ctx.scope.name}\n"
                    f"Authorized repos: {', '.join(ctx.scope.allowed_repos)}\n\n"
                    f"Available tools:\n{json.dumps(tool_catalog, indent=2)}\n\n"
                    f"Initial context:\n{json.dumps(initial_context, indent=2)}"
                ),
            ),
        ]

        result = ReasoningResult(state=dict(initial_context))
        for step in range(1, self.max_steps + 1):
            action, completion = await self._decide(ctx, bus, messages)
            step_record = ReasoningStep(step=step, action=action)

            if action.reasoning:
                await bus.publish(
                    BusEvent.agent_message(
                        ctx.session_id,
                        ctx.agent_id,
                        action.reasoning,
                    )
                )

            if action.action == "message" and action.message:
                await bus.publish(
                    BusEvent.agent_message(ctx.session_id, ctx.agent_id, action.message)
                )

            if action.action == "tool":
                tool = tools.get(action.tool or "")
                if tool is None:
                    tool_result = {"error": f"unknown tool: {action.tool}"}
                else:
                    tool_result = await tool.handler(action.params)
                step_record.tool_result = tool_result
                state_update: object = tool_result.get("_state", {})
                if isinstance(state_update, dict):
                    result.state.update(state_update)
                messages.append(LLMMessage(role="assistant", content=json.dumps(action.model_dump())))
                messages.append(
                    LLMMessage(
                        role="user",
                        content=f"Tool `{action.tool}` result:\n{json.dumps(tool_result, indent=2)[:8000]}",
                    )
                )

            result.steps.append(step_record)

            if action.action == "complete":
                result.completed = True
                result.final_message = action.message
                result.handoff_rationale = action.handoff_rationale
                if action.message:
                    await bus.publish(
                        BusEvent.agent_message(ctx.session_id, ctx.agent_id, action.message)
                    )
                break

        return result

    async def _decide(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        messages: list[LLMMessage],
    ) -> tuple[AgentAction, Any]:
        data, completion = await self.llm.complete_json(messages, temperature=0.2)
        await audit_llm(
            bus,
            ctx.session_id,
            provider=self.llm.provider,
            model=completion.model,
            subagent=None,
            parent_agent=ctx.agent_id,
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            duration_ms=completion.duration_ms,
            status="complete",
            metadata={"phase": "agent_reasoning"},
        )
        return AgentAction.model_validate(data), completion
