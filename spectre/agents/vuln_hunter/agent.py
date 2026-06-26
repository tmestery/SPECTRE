from pathlib import Path

from spectre.agents.base import AgentContext, AgentResult, AgentResultStatus
from spectre.bus.store import FindingsBus
from spectre.schemas.events import BusEvent
from spectre.schemas.finding import Finding, FindingStatus, FindingType, Severity
from spectre.safety.scope import redact_text
from spectre.tools.gitleaks import GitleaksScanner
from spectre.tools.osv_scanner import OsvScanner
from spectre.tools.workflows import WorkflowAnalyzer


class VulnHunterAgent:
    id = "vuln_hunter"
    max_iterations = 1

    async def run(self, ctx: AgentContext, bus: FindingsBus, engagement=None, **deps) -> AgentResult:
        workspace = self._resolve_workspace(ctx, engagement)
        if workspace is None:
            await bus.publish(
                BusEvent.agent_message(
                    ctx.session_id,
                    self.id,
                    "No workspace available for scanning; skipping secret and CVE analysis.",
                )
            )
            return AgentResult(status=AgentResultStatus.EXHAUSTED, message="no workspace")

        await bus.publish(
            BusEvent.agent_message(
                ctx.session_id,
                self.id,
                f"Scanning {ctx.repo} for secrets, dependency CVEs, and workflow misconfigs.",
            )
        )

        findings = await bus.all_findings()
        related_repo = next((f for f in findings if f.type == FindingType.REPOSITORY), None)
        related_ids = [related_repo.id] if related_repo else []

        secret_scanner = GitleaksScanner(bus, ctx.session_id)
        secrets = await secret_scanner.scan(workspace, ctx.repo)
        for match in secrets:
            confidence = 0.92 if match.rule != "generic-api-key" else 0.7
            await bus.publish(
                BusEvent.finding_event(
                    ctx.session_id,
                    Finding(
                        type=FindingType.SECRET,
                        agent=self.id,
                        target=f"{ctx.repo}:{match.file}",
                        severity=Severity.HIGH if confidence >= 0.8 else Severity.MEDIUM,
                        confidence=confidence,
                        title=f"Potential secret ({match.rule})",
                        evidence={
                            "file": match.file,
                            "line": match.line,
                            "rule": match.rule,
                            "snippet_redacted": redact_text(match.match),
                        },
                        related_ids=related_ids,
                        handoff_hint="exploiter",
                    ),
                )
            )

        osv = OsvScanner(bus, ctx.session_id)
        dep_findings = [f for f in findings if f.type == FindingType.DEPENDENCY]
        for dep in dep_findings:
            manifest = dep.evidence.get("path")
            if not manifest:
                continue
            vulns = await osv.scan_manifest(workspace / manifest, ctx.repo)
            for vuln in vulns:
                await bus.publish(
                    BusEvent.finding_event(
                        ctx.session_id,
                        Finding(
                            type=FindingType.VULNERABILITY,
                            agent=self.id,
                            target=f"{ctx.repo}:{vuln.package}@{vuln.version}",
                            severity=Severity.HIGH,
                            confidence=0.85,
                            title=f"{vuln.cve_id} in {vuln.package}",
                            description=vuln.summary,
                            evidence={
                                "cve_id": vuln.cve_id,
                                "package": vuln.package,
                                "version": vuln.version,
                                "exploitability": vuln.exploitability,
                                "manifest": manifest,
                            },
                            related_ids=related_ids + [dep.id],
                            handoff_hint="exploiter",
                        ),
                    )
                )

        workflow_paths = [
            f.evidence.get("path", "")
            for f in findings
            if f.type == FindingType.WORKFLOW and f.evidence.get("path")
        ]
        analyzer = WorkflowAnalyzer()
        for issue in analyzer.analyze_paths(workspace, workflow_paths):
            severity = Severity.HIGH if issue.severity == "high" else Severity.MEDIUM
            await bus.publish(
                BusEvent.finding_event(
                    ctx.session_id,
                    Finding(
                        type=FindingType.MISCONFIGURATION,
                        agent=self.id,
                        target=f"{ctx.repo}:{issue.path}",
                        severity=severity,
                        confidence=0.9,
                        title=f"Workflow issue: {issue.pattern}",
                        description=issue.description,
                        evidence={"path": issue.path, "pattern": issue.pattern},
                        related_ids=related_ids,
                        handoff_hint="exploiter",
                    ),
                )
            )

        total = len(secrets) + len(dep_findings)
        await bus.publish(
            BusEvent.agent_message(
                ctx.session_id,
                self.id,
                f"Scan complete. Found {len(secrets)} secret(s); analyzed {len(dep_findings)} manifest(s).",
            )
        )

        return AgentResult(
            status=AgentResultStatus.COMPLETE,
            message="vuln_hunter complete",
            iterations_used=1,
        )

    def _resolve_workspace(self, ctx: AgentContext, engagement) -> Path | None:
        path = ctx.workspace_path or (engagement.workspace_path if engagement else None)
        if path and Path(path).exists():
            return Path(path)
        return None
