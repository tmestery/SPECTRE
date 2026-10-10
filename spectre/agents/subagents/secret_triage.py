import json
from typing import Any

from spectre.agents.base import AgentContext
from spectre.agents.subagents.base import BaseSubagent
from spectre.bus.store import FindingsBus
from spectre.llm.client import LLMClient
from spectre.llm.prompts import SECRET_TRIAGE
from spectre.llm.types import SubagentResult
from spectre.schemas.finding import Finding, FindingType, Severity


class SecretTriageSubagent(BaseSubagent):
    id = "secret_triage"
    parent_agent = "vuln_hunter"
    task_name = "secret_triage"

    async def run(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        llm: LLMClient,
        context: dict[str, Any],
    ) -> SubagentResult:
        secrets = context.get("secret_findings", [])
        if not secrets:
            return SubagentResult(
                subagent_id=self.id,
                parent_agent=self.parent_agent,
                messages=["No secret findings to triage."],
                status="skipped",
            )

        user_prompt = (
            "Secret findings (redacted evidence only):\n"
            f"{json.dumps(secrets, indent=2)[:12000]}"
        )
        data, _ = await self._complete_json(ctx, bus, llm, system_prompt=SECRET_TRIAGE, user_prompt=user_prompt)

        note = Finding(
            type=FindingType.NOTE,
            agent=ctx.agent_id,
            target=ctx.repo,
            severity=Severity.MEDIUM,
            title="Secret triage summary",
            description=data.get("summary"),
            evidence={"subagent": self.id, "priorities": data.get("priorities", [])},
            handoff_hint="exploiter",
        )
        return SubagentResult(
            subagent_id=self.id,
            parent_agent=self.parent_agent,
            messages=[str(data.get("summary", "Secret triage complete."))],
            findings=[note],
            metadata={"secret_triage": data},
        )
