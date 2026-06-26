from spectre.agents.base import AgentContext, AgentResult, AgentResultStatus
from spectre.agents.cognitive import finding_to_context, get_cognitive_runtime
from spectre.agents.reasoning import AgentReasoningLoop, AgentTool
from spectre.agents.reasoning.prompts import REASONING_RESPONSE_SCHEMA, REPORTER_REASONING
from spectre.agents.routing.registry import CognitiveRuntime
from spectre.bus.store import FindingsBus
from spectre.report.generator import ReportGenerator
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import FindingStatus, FindingType, Severity


class ReporterAgent:
    id = "reporter"
    max_iterations = 6

    def __init__(self, cognitive: CognitiveRuntime | None = None) -> None:
        self._cognitive = cognitive or get_cognitive_runtime()

    async def run(self, ctx: AgentContext, bus: FindingsBus, engagement=None, **deps) -> AgentResult:
        findings = await bus.all_findings()
        events = await bus.all_events()

        if self._cognitive.llm.available:
            tools = self._build_tools(ctx, bus, findings, events)
            reasoning = AgentReasoningLoop(self._cognitive.llm)
            result = await reasoning.run(
                ctx,
                bus,
                system_prompt=REPORTER_REASONING,
                tools=tools,
                initial_context={"finding_count": len(findings)},
                response_schema=REASONING_RESPONSE_SCHEMA,
            )
            return AgentResult(
                status=AgentResultStatus.COMPLETE if result.completed else AgentResultStatus.EXHAUSTED,
                message=result.final_message or "reporter complete",
                iterations_used=len(result.steps),
            )

        return await self._run_deterministic(ctx, bus, findings, events)

    def _build_tools(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        findings: list,
        events: list,
    ) -> dict[str, AgentTool]:
        state: dict = {"executive_summary": None}

        async def review_findings(_: dict) -> dict:
            security = [
                f
                for f in findings
                if f.type
                in {
                    FindingType.SECRET,
                    FindingType.VULNERABILITY,
                    FindingType.MISCONFIGURATION,
                    FindingType.VALIDATION_ATTEMPT,
                }
                and f.status != FindingStatus.FALSE_POSITIVE
            ]
            severity_counts = {level.value: 0 for level in Severity}
            for finding in security:
                severity_counts[finding.severity.value] = (
                    severity_counts.get(finding.severity.value, 0) + 1
                )
            return {
                "severity_counts": severity_counts,
                "top_findings": [finding_to_context(f) for f in security[:12]],
            }

        async def generate_report(_: dict) -> dict:
            pipeline_results = await self._cognitive.router.run_pipeline(
                self.id,
                ctx,
                bus,
                {
                    "severity_counts": state.get("severity_counts", {}),
                    "top_findings": state.get("top_findings", []),
                },
            )
            executive_summary = None
            for sub_result in pipeline_results:
                exec_data = sub_result.metadata.get("executive_summary")
                if isinstance(exec_data, dict):
                    executive_summary = exec_data.get("executive_summary")

            generator = ReportGenerator(ctx.repo, ctx.branch, ctx.scope)
            markdown = generator.render_markdown(
                findings,
                events,
                executive_summary=executive_summary,
            )
            md_path, html_path = generator.write_reports(ctx.session_id, markdown)
            for section in generator.sections:
                await bus.publish(
                    BusEvent(
                        type=EventType.REPORT_SECTION,
                        session_id=ctx.session_id,
                        payload={
                            "section_id": section.id,
                            "title": section.title,
                            "markdown": section.markdown,
                        },
                    )
                )
            return {"markdown_path": str(md_path), "html_path": str(html_path)}

        async def review_and_store(params: dict) -> dict:
            reviewed = await review_findings({})
            state.update(reviewed)
            return reviewed

        return {
            "review_findings": AgentTool(
                name="review_findings",
                description="Summarize current findings by severity for reporting.",
                handler=review_and_store,
            ),
            "generate_report": AgentTool(
                name="generate_report",
                description="Run executive_writer subagent and write markdown/html reports.",
                handler=generate_report,
            ),
        }

    async def _run_deterministic(self, ctx, bus, findings, events) -> AgentResult:
        severity_counts = {level.value: 0 for level in Severity}
        security = [
            f
            for f in findings
            if f.type
            in {
                FindingType.SECRET,
                FindingType.VULNERABILITY,
                FindingType.MISCONFIGURATION,
                FindingType.VALIDATION_ATTEMPT,
            }
            and f.status != FindingStatus.FALSE_POSITIVE
        ]
        for finding in security:
            severity_counts[finding.severity.value] = severity_counts.get(finding.severity.value, 0) + 1

        pipeline_results = await self._cognitive.router.run_pipeline(
            self.id,
            ctx,
            bus,
            {
                "severity_counts": severity_counts,
                "top_findings": [finding_to_context(f) for f in security[:12]],
            },
        )
        executive_summary = None
        for sub_result in pipeline_results:
            exec_data = sub_result.metadata.get("executive_summary")
            if isinstance(exec_data, dict):
                executive_summary = exec_data.get("executive_summary")

        generator = ReportGenerator(ctx.repo, ctx.branch, ctx.scope)
        markdown = generator.render_markdown(findings, events, executive_summary=executive_summary)
        md_path, html_path = generator.write_reports(ctx.session_id, markdown)
        for section in generator.sections:
            await bus.publish(
                BusEvent(
                    type=EventType.REPORT_SECTION,
                    session_id=ctx.session_id,
                    payload={
                        "section_id": section.id,
                        "title": section.title,
                        "markdown": section.markdown,
                    },
                )
            )
        await bus.publish(
            BusEvent.agent_message(
                ctx.session_id,
                self.id,
                f"Report written to {md_path} and {html_path}.",
            )
        )
        return AgentResult(status=AgentResultStatus.COMPLETE, message="reporter complete", iterations_used=1)
