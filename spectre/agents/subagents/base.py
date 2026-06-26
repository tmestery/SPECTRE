from __future__ import annotations

from typing import Any

from spectre.agents.base import AgentContext
from spectre.bus.store import FindingsBus
from spectre.llm.audit import audit_llm
from spectre.llm.client import LLMClient
from spectre.llm.prompts import SPECTRE_SYSTEM
from spectre.llm.router import LLMRouter
from spectre.llm.types import LLMMessage, SubagentResult


class BaseSubagent:
    id: str = "base"
    parent_agent: str = "base"
    task_name: str = "analysis"

    async def run(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        llm: LLMClient,
        context: dict[str, Any],
    ) -> SubagentResult:
        raise NotImplementedError

    async def _complete_json(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        llm: LLMClient,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[dict[str, Any], SubagentResult]:
        router = LLMRouter(llm.model)
        route = router.route(self.task_name)
        messages = [
            LLMMessage(role="system", content=f"{SPECTRE_SYSTEM}\n{system_prompt}"),
            LLMMessage(
                role="user",
                content=(
                    f"Engagement scope: {ctx.scope.name}\n"
                    f"Authorized repos: {', '.join(ctx.scope.allowed_repos)}\n"
                    f"Target: {ctx.repo}@{ctx.branch}\n\n"
                    f"{user_prompt}"
                ),
            ),
        ]
        try:
            data, result = await llm.complete_json(messages, temperature=route.temperature)
            await audit_llm(
                bus,
                ctx.session_id,
                provider=llm.provider,
                model=result.model,
                subagent=self.id,
                parent_agent=self.parent_agent,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                duration_ms=result.duration_ms,
                status="complete",
            )
            return data, SubagentResult(
                subagent_id=self.id,
                parent_agent=self.parent_agent,
                status="complete",
            )
        except Exception as exc:
            await audit_llm(
                bus,
                ctx.session_id,
                provider=llm.provider,
                model=llm.model,
                subagent=self.id,
                parent_agent=self.parent_agent,
                prompt_tokens=0,
                completion_tokens=0,
                duration_ms=0,
                status="failed",
                metadata={"error": str(exc)},
            )
            raise
