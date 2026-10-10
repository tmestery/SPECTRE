from pathlib import Path

from spectre.agents.base import AgentContext, AgentResult, AgentResultStatus
from spectre.agents.context import findings_by_types
from spectre.agents.cognitive import get_cognitive_runtime
from spectre.agents.reasoning import AgentReasoningLoop, AgentTool
from spectre.agents.reasoning.prompts import REASONING_RESPONSE_SCHEMA, VULN_HUNTER_REASONING
from spectre.agents.routing.registry import CognitiveRuntime
from spectre.bus.store import FindingsBus
from spectre.schemas.events import BusEvent
from spectre.schemas.finding import Finding, FindingType, Severity
from spectre.safety.scope import redact_text
from spectre.tools.gitleaks import GitleaksScanner
from spectre.tools.osv_scanner import OsvScanner
from spectre.tools.workflows import WorkflowAnalyzer


class VulnHunterAgent:
    id = "vuln_hunter"
    max_iterations = 6

    def __init__(self, cognitive: CognitiveRuntime | None = None) -> None:
        self._cognitive = cognitive or get_cognitive_runtime()

    async def run(self, ctx: AgentContext, bus: FindingsBus, engagement=None, **deps) -> AgentResult:
        workspace = await self._ensure_workspace(ctx, bus, engagement)
        if workspace is None:
            await bus.publish(
                BusEvent.agent_message(
                    ctx.session_id,
                    self.id,
                    "No workspace available for scanning; skipping secret and CVE analysis.",
                )
            )
            return AgentResult(status=AgentResultStatus.EXHAUSTED, message="no workspace")

        findings = await bus.all_findings()
        recon_context = {
            "repository_findings": len([f for f in findings if f.type == FindingType.REPOSITORY]),
            "workflow_count": len([f for f in findings if f.type == FindingType.WORKFLOW]),
            "dependency_manifests": [
                f.evidence.get("path")
                for f in findings
                if f.type == FindingType.DEPENDENCY and f.evidence.get("path")
            ],
            "focus_notes": [
                f.description for f in findings if f.type == FindingType.NOTE and f.agent == "recon"
            ],
        }

        state = {"secrets": 0, "vulns": 0, "misconfigs": 0}

        if self._cognitive.llm.available:
            tools = self._build_tools(ctx, bus, workspace, findings, state)
            reasoning = AgentReasoningLoop(self._cognitive.llm)
            result = await reasoning.run(
                ctx,
                bus,
                system_prompt=VULN_HUNTER_REASONING,
                tools=tools,
                initial_context=recon_context,
                response_schema=REASONING_RESPONSE_SCHEMA,
            )
            all_findings = await bus.all_findings()
            await self._run_subagents(ctx, bus, all_findings)
            return AgentResult(
                status=AgentResultStatus.COMPLETE if result.completed else AgentResultStatus.EXHAUSTED,
                message=result.final_message or "vuln_hunter complete",
                iterations_used=len(result.steps),
            )

        return await self._run_deterministic(ctx, bus, workspace, findings)

    def _build_tools(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        workspace: Path,
        findings: list,
        state: dict,
    ) -> dict[str, AgentTool]:
        related_repo = next((f for f in findings if f.type == FindingType.REPOSITORY), None)
        related_ids = [related_repo.id] if related_repo else []

        async def scan_secrets(_: dict) -> dict:
            scanner = GitleaksScanner(bus, ctx.session_id)
            matches = await scanner.scan(workspace, ctx.repo)
            for match in matches:
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
            state["secrets"] = len(matches)
            return {"secret_count": len(matches)}

        async def scan_dependencies(_: dict) -> dict:
            osv = OsvScanner(bus, ctx.session_id)
            dep_findings = [f for f in findings if f.type == FindingType.DEPENDENCY]
            vuln_count = 0
            for dep in dep_findings:
                manifest = dep.evidence.get("path")
                if not manifest:
                    continue
                vulns = await osv.scan_manifest(workspace / manifest, ctx.repo)
                for vuln in vulns:
                    vuln_count += 1
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
            state["vulns"] = vuln_count
            return {"vulnerability_count": vuln_count, "manifests_scanned": len(dep_findings)}

        async def scan_workflows(_: dict) -> dict:
            workflow_paths = [
                f.evidence.get("path", "")
                for f in findings
                if f.type == FindingType.WORKFLOW and f.evidence.get("path")
            ]
            analyzer = WorkflowAnalyzer()
            misconfig_count = 0
            for issue in analyzer.analyze_paths(workspace, workflow_paths):
                misconfig_count += 1
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
            state["misconfigs"] = misconfig_count
            return {"misconfiguration_count": misconfig_count}

        return {
            "scan_secrets": AgentTool(
                name="scan_secrets",
                description="Run gitleaks secret scan on the cloned workspace.",
                handler=scan_secrets,
            ),
            "scan_dependencies": AgentTool(
                name="scan_dependencies",
                description="Run osv-scanner on dependency manifests discovered by Recon.",
                handler=scan_dependencies,
            ),
            "scan_workflows": AgentTool(
                name="scan_workflows",
                description="Analyze GitHub Actions workflows for risky patterns.",
                handler=scan_workflows,
            ),
        }

    async def _run_subagents(self, ctx: AgentContext, bus: FindingsBus, all_findings: list) -> None:
        await self._cognitive.router.run_pipeline(
            self.id,
            ctx,
            bus,
            {
                "secret_findings": findings_by_types(all_findings, {FindingType.SECRET}),
                "vulnerability_findings": findings_by_types(all_findings, {FindingType.VULNERABILITY}),
                "misconfiguration_findings": findings_by_types(
                    all_findings, {FindingType.MISCONFIGURATION}
                ),
            },
        )

    async def _run_deterministic(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        workspace: Path,
        findings: list,
    ) -> AgentResult:
        state = {}
        tools = self._build_tools(ctx, bus, workspace, findings, state)
        await tools["scan_secrets"].handler({})
        await tools["scan_dependencies"].handler({})
        await tools["scan_workflows"].handler({})
        await bus.publish(
            BusEvent.agent_message(
                ctx.session_id,
                self.id,
                (
                    f"Scan complete. Found {state.get('secrets', 0)} secret(s); "
                    f"{state.get('vulns', 0)} CVE(s); {state.get('misconfigs', 0)} workflow issue(s)."
                ),
            )
        )
        all_findings = await bus.all_findings()
        await self._run_subagents(ctx, bus, all_findings)
        return AgentResult(status=AgentResultStatus.COMPLETE, message="vuln_hunter complete", iterations_used=1)

    def _resolve_workspace(self, ctx: AgentContext, engagement) -> Path | None:
        path = ctx.workspace_path or (engagement.workspace_path if engagement else None)
        if path and Path(path).exists():
            return Path(path)
        return None

    async def _ensure_workspace(self, ctx: AgentContext, bus: FindingsBus, engagement) -> Path | None:
        workspace = self._resolve_workspace(ctx, engagement)
        if workspace is not None:
            return workspace

        if engagement is None:
            return None

        import httpx

        from spectre.safety.scope import ScopeEnforcer
        from spectre.tools.github import GitHubClient

        enforcer = ScopeEnforcer(ctx.scope)
        github = GitHubClient(bus, ctx.session_id, enforcer)
        try:
            await bus.publish(
                BusEvent.agent_message(
                    ctx.session_id,
                    self.id,
                    f"No workspace from Recon; cloning {ctx.repo} for secret and CVE scans.",
                )
            )
            inventory = await github.inventory_repo(ctx.repo, ctx.branch)
            if inventory.clone_path:
                engagement.workspace_path = str(inventory.clone_path)
                ctx.workspace_path = engagement.workspace_path
                return inventory.clone_path
        except httpx.HTTPError:
            return None
        finally:
            await github.close()
        return None
