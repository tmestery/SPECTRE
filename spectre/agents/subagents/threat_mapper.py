import json
from typing import Any

from spectre.agents.subagents.base import BaseSubagent
from spectre.agents.base import AgentContext
from spectre.bus.store import FindingsBus
from spectre.llm.client import LLMClient
from spectre.llm.prompts import THREAT_MAPPER
from spectre.llm.types import SubagentResult
from spectre.schemas.finding import Finding, FindingType, Severity


class ThreatMapperSubagent(BaseSubagent):
    id = "threat_mapper"
    parent_agent = "vuln_hunter"
    task_name = "threat_mapping"

    async def run(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        llm: LLMClient,
        context: dict[str, Any],
    ) -> SubagentResult:
        signals = {
            "secret_count": len(context.get("secret_findings", [])),
            "cve_count": len(context.get("vulnerability_findings", [])),
            "misconfig_count": len(context.get("misconfiguration_findings", [])),
            "surface_analysis": context.get("surface_analysis"),
        }
        user_prompt = f"Engagement signals JSON:\n{json.dumps(signals, indent=2)}"
        data, _ = await self._complete_json(ctx, bus, llm, system_prompt=THREAT_MAPPER, user_prompt=user_prompt)

        note = Finding(
            type=FindingType.NOTE,
            agent=ctx.agent_id,
            target=ctx.repo,
            severity=Severity.INFO,
            title="Threat map",
            description=data.get("summary"),
            evidence={"subagent": self.id, "themes": data.get("themes", [])},
        )
        return SubagentResult(
            subagent_id=self.id,
            parent_agent=self.parent_agent,
            messages=[str(data.get("summary", "Threat mapping complete."))],
            findings=[note],
            metadata={"threat_map": data},
        )
