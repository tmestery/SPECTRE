
from spectre.agents.base import AgentContext, AgentResult, AgentResultStatus
from spectre.agents.reasoning import AgentReasoningLoop, AgentTool
from spectre.agents.reasoning.prompts import REASONING_RESPONSE_SCHEMA, RECON_REASONING
from spectre.agents.routing.registry import CognitiveRuntime
from spectre.bus.store import FindingsBus
from spectre.safety.scope import ScopeEnforcer
from spectre.schemas.events import BusEvent
from spectre.schemas.finding import Finding, FindingType, Severity
from spectre.tools.github import GitHubClient, RepoInventory


async def publish_inventory_findings(
    ctx: AgentContext,
    bus: FindingsBus,
    inventory: RepoInventory,
) -> Finding:
    repo_finding = Finding(
        type=FindingType.REPOSITORY,
        agent=ctx.agent_id,
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
                    agent=ctx.agent_id,
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
                    agent=ctx.agent_id,
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
                    agent=ctx.agent_id,
                    target=f"{ctx.repo}:{dep_path}",
                    severity=Severity.INFO,
                    title=f"Dependency manifest: {dep_path}",
                    evidence={"path": dep_path, "repo": ctx.repo},
                    related_ids=[repo_finding.id],
                    handoff_hint="vuln_hunter",
                ),
            )
        )
    return repo_finding


class ReconAgent:
    id = "recon"
    max_iterations = 6

    def __init__(self, cognitive: CognitiveRuntime | None = None) -> None:
        from spectre.agents.cognitive import get_cognitive_runtime

        self._cognitive = cognitive or get_cognitive_runtime()

    async def run(self, ctx: AgentContext, bus: FindingsBus, engagement=None, **deps) -> AgentResult:
        enforcer = ScopeEnforcer(ctx.scope)
        github = GitHubClient(bus, ctx.session_id, enforcer)
        state: dict = {"inventory": None}

        try:
            if self._cognitive.llm.available:
                try:
                    tools = self._build_tools(ctx, bus, github, engagement, state)
                    reasoning = AgentReasoningLoop(self._cognitive.llm)
                    result = await reasoning.run(
                        ctx,
                        bus,
                        system_prompt=RECON_REASONING,
                        tools=tools,
                        initial_context={"repo": ctx.repo, "branch": ctx.branch},
                        response_schema=REASONING_RESPONSE_SCHEMA,
                    )
                    inventory = state.get("inventory")
                    if inventory and engagement is not None and inventory.clone_path:
                        engagement.workspace_path = str(inventory.clone_path)
                    if inventory:
                        await self._run_subagents(ctx, bus, inventory)
                        return AgentResult(
                            status=(
                                AgentResultStatus.COMPLETE
                                if result.completed
                                else AgentResultStatus.EXHAUSTED
                            ),
                            message=result.final_message or "recon complete",
                            iterations_used=len(result.steps),
                        )
                    # LLM ran but never mapped the repo — fall through to deterministic.
                    await bus.publish(
                        BusEvent.agent_message(
                            ctx.session_id,
                            self.id,
                            "LLM reasoning did not map the repository; falling back to deterministic recon.",
                        )
                    )
                except Exception as exc:
                    await bus.publish(
                        BusEvent.agent_message(
                            ctx.session_id,
                            self.id,
                            f"LLM unavailable ({exc}); falling back to deterministic recon.",
                        )
                    )

            return await self._run_deterministic(ctx, bus, github, engagement)
        finally:
            await github.close()

    def _build_tools(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        github: GitHubClient,
        engagement,
        state: dict,
    ) -> dict[str, AgentTool]:
        async def map_repository(_: dict) -> dict:
            inventory = await github.inventory_repo(ctx.repo, ctx.branch)
            state["inventory"] = inventory
            await publish_inventory_findings(ctx, bus, inventory)
            if inventory.clone_path and engagement is not None:
                engagement.workspace_path = str(inventory.clone_path)
            return {
                "repo": inventory.repo,
                "file_count": len(inventory.files),
                "workflow_count": len(inventory.workflows),
                "dependency_manifests": inventory.dependencies,
                "languages": inventory.languages,
            }

        async def record_focus_areas(params: dict) -> dict:
            areas = params.get("focus_areas", [])
            note = Finding(
                type=FindingType.NOTE,
                agent=ctx.agent_id,
                target=ctx.repo,
                severity=Severity.INFO,
                title="Recon focus areas",
                description=params.get("summary"),
                evidence={"focus_areas": areas},
                handoff_hint="vuln_hunter",
            )
            await bus.publish(BusEvent.finding_event(ctx.session_id, note))
            return {"recorded": areas}

        return {
            "map_repository": AgentTool(
                name="map_repository",
                description="Clone and map repository structure, files, workflows, and dependency manifests.",
                handler=map_repository,
            ),
            "record_focus_areas": AgentTool(
                name="record_focus_areas",
                description="Record prioritized attack surface areas for VulnHunter.",
                handler=record_focus_areas,
                parameters={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "focus_areas": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["summary", "focus_areas"],
                },
            ),
        }

    async def _run_subagents(self, ctx: AgentContext, bus: FindingsBus, inventory: RepoInventory) -> None:
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

    async def _run_deterministic(
        self,
        ctx: AgentContext,
        bus: FindingsBus,
        github: GitHubClient,
        engagement,
    ) -> AgentResult:
        await bus.publish(
            BusEvent.agent_message(
                ctx.session_id,
                self.id,
                f"Mapping {ctx.repo} on branch {ctx.branch} via GitHub API.",
            )
        )
        inventory = await github.inventory_repo(ctx.repo, ctx.branch)
        await publish_inventory_findings(ctx, bus, inventory)
        if inventory.clone_path and engagement is not None:
            engagement.workspace_path = str(inventory.clone_path)
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
        await self._run_subagents(ctx, bus, inventory)
        return AgentResult(status=AgentResultStatus.COMPLETE, message="recon complete", iterations_used=1)
