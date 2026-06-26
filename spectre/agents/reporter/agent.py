from spectre.agents.base import AgentContext, AgentResult, AgentResultStatus
from spectre.agents.cognitive import finding_to_context, get_cognitive_runtime
from spectre.agents.routing.registry import CognitiveRuntime
from spectre.bus.store import FindingsBus
from spectre.report.generator import ReportGenerator
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import FindingStatus, FindingType, Severity


class ReporterAgent:
    id = "reporter"
    max_iterations = 1

    def __init__(self, cognitive: CognitiveRuntime | None = None) -> None:
        self._cognitive = cognitive or get_cognitive_runtime()

    async def run(self, ctx: AgentContext, bus: FindingsBus, engagement=None, **deps) -> AgentResult:
        await bus.publish(
            BusEvent.agent_message(
                ctx.session_id,
                self.id,
                f"Synthesizing security report for {ctx.repo} @ {ctx.branch}.",
            )
        )

        findings = await bus.all_findings()
        events = await bus.all_events()
        severity_counts = {level.value: 0 for level in Severity}
        for finding in findings:
            if finding.type in {
                FindingType.SECRET,
                FindingType.VULNERABILITY,
                FindingType.MISCONFIGURATION,
                FindingType.VALIDATION_ATTEMPT,
            }:
                severity_counts[finding.severity.value] = (
                    severity_counts.get(finding.severity.value, 0) + 1
                )

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
        security.sort(key=lambda item: item.severity.value, reverse=True)

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
        for result in pipeline_results:
            exec_data = result.metadata.get("executive_summary")
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

        await bus.publish(
            BusEvent.agent_message(
                ctx.session_id,
                self.id,
                f"Report written to {md_path} and {html_path}.",
            )
        )

        return AgentResult(
            status=AgentResultStatus.COMPLETE,
            message="reporter complete",
            iterations_used=1,
        )
