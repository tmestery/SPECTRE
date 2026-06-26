import json
from typing import Any

from spectre.agents.subagents.base import BaseSubagent
from spectre.agents.base import AgentContext
from spectre.bus.store import FindingsBus
from spectre.llm.client import LLMClient
from spectre.llm.prompts import EXECUTIVE_WRITER
from spectre.llm.types import SubagentResult
from spectre.schemas.finding import Finding, FindingType, Severity


class ExecutiveWriterSubagent(BaseSubagent):
    id = "executive_writer"
    parent_agent = "reporter"
    task_name = "executive_summary"

    async def run(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        llm: LLMClient,
        context: dict[str, Any],
    ) -> SubagentResult:
        summary_input = {
            "severity_counts": context.get("severity_counts", {}),
            "top_findings": context.get("top_findings", []),
            "validation_review": context.get("validation_review"),
            "threat_map": context.get("threat_map"),
        }
        user_prompt = f"Audit rollup JSON:\n{json.dumps(summary_input, indent=2)[:12000]}"
        data, _ = await self._complete_json(
            ctx, bus, llm, system_prompt=EXECUTIVE_WRITER, user_prompt=user_prompt
        )

        note = Finding(
            type=FindingType.NOTE,
            agent=ctx.agent_id,
            target=ctx.repo,
            severity=Severity.INFO,
            title="Executive summary (LLM)",
            description=data.get("executive_summary"),
            evidence={
                "subagent": self.id,
                "top_risks": data.get("top_risks", []),
                "recommended_actions": data.get("recommended_actions", []),
            },
        )
        return SubagentResult(
            subagent_id=self.id,
            parent_agent=self.parent_agent,
            messages=[str(data.get("executive_summary", "Executive summary complete."))],
            findings=[note],
            metadata={"executive_summary": data},
        )
