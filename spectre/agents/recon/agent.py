from pathlib import Path

from spectre.agents.base import AgentContext, AgentResult, AgentResultStatus
from spectre.agents.routing.registry import CognitiveRuntime
from spectre.bus.store import FindingsBus
from spectre.schemas.events import BusEvent
from spectre.schemas.finding import Finding, FindingType, Severity
from spectre.safety.scope import ScopeEnforcer
from spectre.tools.github import GitHubClient


class ReconAgent:
    id = "recon"
    max_iterations = 1

    def __init__(self, cognitive: CognitiveRuntime | None = None) -> None:
        from spectre.agents.cognitive import get_cognitive_runtime

        self._cognitive = cognitive or get_cognitive_runtime()

    async def run(self, ctx: AgentContext, bus: FindingsBus, engagement=None, **deps) -> AgentResult:
        enforcer = ScopeEnforcer(ctx.scope)
        github = GitHubClient(bus, ctx.session_id, enforcer)
        try:
            await bus.publish(
                BusEvent.agent_message(
                    ctx.session_id,
                    self.id,
                    f"Mapping {ctx.repo} on branch {ctx.branch} via GitHub API.",
                )
            )
            inventory = await github.inventory_repo(ctx.repo, ctx.branch)

            repo_finding = Finding(
                type=FindingType.REPOSITORY,
                agent=self.id,
                target=ctx.repo,
                severity=Severity.INFO,
                title=f"Repository mapped: {ctx.repo}",
                description=inventory.metadata.get("description"),
                evidence={
                    "branch": ctx.branch,
                    "default_branch": inventory.default_branch,
                    "languages": inventory.languages,
                    "file_count": len(inventory.files),
                    "html_url": inventory.metadata.get("html_url"),
                },
                handoff_hint="vuln_hunter",
            )
            await bus.publish(BusEvent.finding_event(ctx.session_id, repo_finding))

            for path in inventory.files[:100]:
                await bus.publish(
                    BusEvent.finding_event(
                        ctx.session_id,
                        Finding(
                            type=FindingType.FILE,
                            agent=self.id,
                            target=f"{ctx.repo}:{path}",
                            severity=Severity.INFO,
                            title=f"Tracked file: {path}",
                            evidence={"path": path, "repo": ctx.repo},
                            related_ids=[repo_finding.id],
                        ),
                    )
                )

            for workflow in inventory.workflows:
                await bus.publish(
                    BusEvent.finding_event(
                        ctx.session_id,
                        Finding(
                            type=FindingType.WORKFLOW,
                            agent=self.id,
                            target=f"{ctx.repo}:{workflow}",
                            severity=Severity.INFO,
                            title=f"Workflow: {workflow}",
                            evidence={"path": workflow, "repo": ctx.repo},
                            related_ids=[repo_finding.id],
                            handoff_hint="vuln_hunter",
                        ),
                    )
                )

            for dep_path in inventory.dependencies:
                await bus.publish(
                    BusEvent.finding_event(
                        ctx.session_id,
                        Finding(
                            type=FindingType.DEPENDENCY,
                            agent=self.id,
                            target=f"{ctx.repo}:{dep_path}",
                            severity=Severity.INFO,
                            title=f"Dependency manifest: {dep_path}",
                            evidence={"path": dep_path, "repo": ctx.repo},
                            related_ids=[repo_finding.id],
                            handoff_hint="vuln_hunter",
                        ),
                    )
                )

            await bus.publish(
                BusEvent.agent_message(
                    ctx.session_id,
                    self.id,
                    (
                        f"Mapped {len(inventory.files)} files, {len(inventory.workflows)} workflows, "
                        f"{len(inventory.dependencies)} dependency manifests. Handing off to VulnHunter."
                    ),
                )
            )

            if inventory.clone_path and engagement is not None:
                engagement.workspace_path = str(inventory.clone_path)

            await self._cognitive.router.run_pipeline(
                self.id,
                ctx,
                bus,
                {
                    "inventory": {
                        "repo": inventory.repo,
                        "branch": inventory.branch,
                        "default_branch": inventory.default_branch,
                        "languages": inventory.languages,
                        "file_count": len(inventory.files),
                        "workflows": inventory.workflows,
                        "dependencies": inventory.dependencies,
                        "sample_files": inventory.files[:40],
                    }
                },
            )

            return AgentResult(
                status=AgentResultStatus.COMPLETE,
                message="recon complete",
                iterations_used=1,
            )
        finally:
            await github.close()
