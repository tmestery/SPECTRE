from spectre.agents.base import AgentContext, AgentResult, AgentResultStatus
from spectre.bus.store import FindingsBus
from spectre.report.generator import ReportGenerator
from spectre.schemas.events import BusEvent, EventType


class ReporterAgent:
    id = "reporter"
    max_iterations = 1

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
        generator = ReportGenerator(ctx.repo, ctx.branch, ctx.scope)
        markdown = generator.render_markdown(findings, events)
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
