import json
from typing import Any

from spectre.agents.base import AgentContext
from spectre.agents.subagents.base import BaseSubagent
from spectre.bus.store import FindingsBus
from spectre.llm.client import LLMClient
from spectre.llm.prompts import CVE_PRIORITIZER
from spectre.llm.types import SubagentResult
from spectre.schemas.finding import Finding, FindingType, Severity


class CVEPrioritizerSubagent(BaseSubagent):
    id = "cve_prioritizer"
    parent_agent = "vuln_hunter"
    task_name = "cve_prioritization"

    async def run(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        llm: LLMClient,
        context: dict[str, Any],
    ) -> SubagentResult:
        vulns = context.get("vulnerability_findings", [])
        if not vulns:
            return SubagentResult(
                subagent_id=self.id,
                parent_agent=self.parent_agent,
                messages=["No CVE findings to prioritize."],
                status="skipped",
            )

        user_prompt = f"CVE findings JSON:\n{json.dumps(vulns, indent=2)[:12000]}"
        data, _ = await self._complete_json(ctx, bus, llm, system_prompt=CVE_PRIORITIZER, user_prompt=user_prompt)

        note = Finding(
            type=FindingType.NOTE,
            agent=ctx.agent_id,
            target=ctx.repo,
            severity=Severity.INFO,
            title="CVE prioritization",
            description=data.get("summary"),
            evidence={"subagent": self.id, "ranked": data.get("ranked", [])},
            handoff_hint="exploiter",
        )
        return SubagentResult(
            subagent_id=self.id,
            parent_agent=self.parent_agent,
            messages=[str(data.get("summary", "CVE prioritization complete."))],
            findings=[note],
            metadata={"cve_prioritization": data},
        )
