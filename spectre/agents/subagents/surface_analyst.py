import json
from typing import Any

from spectre.agents.subagents.base import BaseSubagent
from spectre.agents.base import AgentContext
from spectre.bus.store import FindingsBus
from spectre.llm.client import LLMClient
from spectre.llm.prompts import SURFACE_ANALYST
from spectre.llm.types import SubagentResult
from spectre.schemas.finding import Finding, FindingType, Severity


class SurfaceAnalystSubagent(BaseSubagent):
    id = "surface_analyst"
    parent_agent = "recon"
    task_name = "surface_analysis"

    async def run(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        llm: LLMClient,
        context: dict[str, Any],
    ) -> SubagentResult:
        inventory = context.get("inventory", {})
        user_prompt = (
            "Repository inventory JSON:\n"
            f"{json.dumps(inventory, indent=2)[:12000]}\n"
            "Summarize attack surface and what VulnHunter should prioritize."
        )
        data, _ = await self._complete_json(ctx, bus, llm, system_prompt=SURFACE_ANALYST, user_prompt=user_prompt)

        note = Finding(
            type=FindingType.NOTE,
            agent=ctx.agent_id,
            target=ctx.repo,
            severity=Severity.INFO,
            title="Attack surface analysis",
            description=data.get("summary"),
            evidence={
                "subagent": self.id,
                "risk_areas": data.get("risk_areas", []),
                "recommended_focus": data.get("recommended_focus"),
            },
            handoff_hint="vuln_hunter",
        )
        return SubagentResult(
            subagent_id=self.id,
            parent_agent=self.parent_agent,
            messages=[str(data.get("summary", "Attack surface analysis complete."))],
            findings=[note],
            metadata={"surface_analysis": data},
        )
