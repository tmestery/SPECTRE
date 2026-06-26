import json
from typing import Any

from spectre.agents.subagents.base import BaseSubagent
from spectre.agents.base import AgentContext
from spectre.bus.store import FindingsBus
from spectre.llm.client import LLMClient
from spectre.llm.prompts import VALIDATION_ADVISOR
from spectre.llm.types import SubagentResult
from spectre.schemas.finding import Finding, FindingType, Severity


class ValidationAdvisorSubagent(BaseSubagent):
    id = "validation_advisor"
    parent_agent = "exploiter"
    task_name = "validation_review"

    async def run(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        llm: LLMClient,
        context: dict[str, Any],
    ) -> SubagentResult:
        validations = context.get("validation_findings", [])
        if not validations:
            return SubagentResult(
                subagent_id=self.id,
                parent_agent=self.parent_agent,
                messages=["No validation results to review."],
                status="skipped",
            )

        user_prompt = f"Validation attempts JSON:\n{json.dumps(validations, indent=2)[:12000]}"
        data, _ = await self._complete_json(
            ctx, bus, llm, system_prompt=VALIDATION_ADVISOR, user_prompt=user_prompt
        )

        note = Finding(
            type=FindingType.NOTE,
            agent=ctx.agent_id,
            target=ctx.repo,
            severity=Severity.INFO,
            title="Validation review",
            description=data.get("narrative"),
            evidence={
                "subagent": self.id,
                "confirmed_count": data.get("confirmed_count"),
                "false_positive_risk": data.get("false_positive_risk"),
            },
            handoff_hint="reporter",
        )
        return SubagentResult(
            subagent_id=self.id,
            parent_agent=self.parent_agent,
            messages=[str(data.get("summary", "Validation review complete."))],
            findings=[note],
            metadata={"validation_review": data},
        )
