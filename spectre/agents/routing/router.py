from __future__ import annotations

from spectre.agents.base import AgentContext
from spectre.agents.subagents.base import BaseSubagent
from spectre.agents.subagents.cve_prioritizer import CVEPrioritizerSubagent
from spectre.agents.subagents.executive_writer import ExecutiveWriterSubagent
from spectre.agents.subagents.secret_triage import SecretTriageSubagent
from spectre.agents.subagents.surface_analyst import SurfaceAnalystSubagent
from spectre.agents.subagents.threat_mapper import ThreatMapperSubagent
from spectre.agents.subagents.validation_advisor import ValidationAdvisorSubagent
from spectre.bus.store import FindingsBus
from spectre.llm.client import LLMClient
from spectre.llm.types import SubagentResult
from spectre.schemas.events import BusEvent, EventType

AGENT_PIPELINES: dict[str, list[str]] = {
    "recon": ["surface_analyst"],
    "vuln_hunter": ["secret_triage", "cve_prioritizer", "threat_mapper"],
    "exploiter": ["validation_advisor"],
    "reporter": ["executive_writer"],
}


class SubagentRegistry:
    def __init__(self) -> None:
        self._subagents: dict[tuple[str, str], BaseSubagent] = {}
        for subagent in (
            SurfaceAnalystSubagent(),
            SecretTriageSubagent(),
            CVEPrioritizerSubagent(),
            ThreatMapperSubagent(),
            ValidationAdvisorSubagent(),
            ExecutiveWriterSubagent(),
        ):
            self._subagents[(subagent.parent_agent, subagent.id)] = subagent

    def get(self, parent_agent: str, subagent_id: str) -> BaseSubagent:
        key = (parent_agent, subagent_id)
        if key not in self._subagents:
            raise KeyError(f"unknown subagent: {parent_agent}/{subagent_id}")
        return self._subagents[key]

    def pipeline_for(self, parent_agent: str) -> list[str]:
        return list(AGENT_PIPELINES.get(parent_agent, []))


class AgentCognitiveRouter:
    """Routes parent agents to LLM-backed subagent pipelines after tool execution."""

    def __init__(self, llm: LLMClient, registry: SubagentRegistry | None = None) -> None:
        self.llm = llm
        self.registry = registry or SubagentRegistry()

    @property
    def available(self) -> bool:
        return self.llm.available

    async def run_pipeline(
        self,
        parent_agent: str,
        ctx: AgentContext,
        bus: FindingsBus,
        context: dict,
    ) -> list[SubagentResult]:
        if not self.available:
            await bus.publish(
                BusEvent.agent_message(
                    ctx.session_id,
                    parent_agent,
                    "LLM not configured; skipping cognitive subagent pipeline.",
                )
            )
            return []

        results: list[SubagentResult] = []
        for subagent_id in self.registry.pipeline_for(parent_agent):
            subagent = self.registry.get(parent_agent, subagent_id)
            await bus.publish(
                BusEvent(
                    type=EventType.SUBAGENT_ACTIVATED,
                    session_id=ctx.session_id,
                    payload={
                        "parent_agent": parent_agent,
                        "subagent": subagent_id,
                        "activation_id": f"sub_{ctx.activation_id}_{subagent_id}",
                    },
                )
            )
            try:
                result = await subagent.run(ctx, bus, self.llm, context)
            except Exception as exc:
                result = SubagentResult(
                    subagent_id=subagent_id,
                    parent_agent=parent_agent,
                    messages=[f"Subagent {subagent_id} failed: {exc}"],
                    status="failed",
                    metadata={"error": str(exc)},
                )
            results.append(result)
            await self._publish_result(ctx, bus, result)
            context = {**context, **result.metadata}
        return results

    async def _publish_result(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        result: SubagentResult,
    ) -> None:
        for message in result.messages:
            await bus.publish(
                BusEvent.agent_message(
                    ctx.session_id,
                    result.parent_agent,
                    message,
                    subagent=result.subagent_id,
                )
            )
        for finding in result.findings:
            await bus.publish(BusEvent.finding_event(ctx.session_id, finding))
