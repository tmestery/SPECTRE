import pytest

from spectre.orchestrator.handoffs import HandoffEngine
from spectre.schemas.engagement import AgentResult, AgentResultStatus, Engagement
from spectre.schemas.finding import Finding, FindingType
from spectre.schemas.scope import RepoScope


def _engagement() -> Engagement:
    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    return Engagement(repo="tmestery/SPECTRE", branch="main", scope=scope)


@pytest.mark.asyncio
async def test_repo_mapped_handoff():
    engine = HandoffEngine(_engagement().scope)
    findings = [
        Finding(type=FindingType.REPOSITORY, agent="recon", target="tmestery/SPECTRE", title="repo"),
        Finding(type=FindingType.FILE, agent="recon", target="tmestery/SPECTRE:README.md", title="file"),
    ]

    class FakeBus:
        async def all_findings(self):
            return findings

    decision = await engine.evaluate(
        FakeBus(),
        "recon",
        AgentResult(status=AgentResultStatus.COMPLETE),
        _engagement(),
    )
    assert decision.rule == "repo_mapped"
    assert decision.to_agent == "vuln_hunter"


@pytest.mark.asyncio
async def test_out_of_scope_repo_does_not_handoff_to_vuln():
    engine = HandoffEngine(RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"]))
    findings = [
        Finding(type=FindingType.REPOSITORY, agent="recon", target="octocat/Hello-World", title="repo"),
        Finding(type=FindingType.FILE, agent="recon", target="octocat/Hello-World:README.md", title="file"),
    ]

    class FakeBus:
        async def all_findings(self):
            return findings

    decision = await engine.evaluate(
        FakeBus(),
        "recon",
        AgentResult(status=AgentResultStatus.COMPLETE),
        _engagement(),
    )
    assert decision.to_agent == "reporter"


@pytest.mark.asyncio
async def test_low_confidence_secret_no_exploiter_handoff():
    engine = HandoffEngine(_engagement().scope)
    findings = [
        Finding(
            type=FindingType.SECRET,
            agent="vuln_hunter",
            target="x",
            title="maybe",
            confidence=0.2,
        )
    ]

    class FakeBus:
        async def all_findings(self):
            return findings

    decision = await engine.evaluate(
        FakeBus(),
        "vuln_hunter",
        AgentResult(status=AgentResultStatus.EXHAUSTED),
        _engagement(),
    )
    assert decision.to_agent == "reporter"


@pytest.mark.asyncio
async def test_timeout_routes_to_reporter():
    engagement = _engagement()
    engagement.max_duration_minutes = 0
    engine = HandoffEngine(engagement.scope)

    class FakeBus:
        async def all_findings(self):
            return []

    decision = await engine.evaluate(
        FakeBus(),
        "recon",
        AgentResult(status=AgentResultStatus.COMPLETE),
        engagement,
    )
    assert decision.rule == "engagement_timeout"
    assert decision.to_agent == "reporter"


@pytest.mark.asyncio
async def test_handoff_decision_has_required_fields():
    engine = HandoffEngine(_engagement().scope)
    findings = [
        Finding(type=FindingType.REPOSITORY, agent="recon", target="tmestery/SPECTRE", title="repo"),
        Finding(type=FindingType.DEPENDENCY, agent="recon", target="tmestery/SPECTRE:package.json", title="dep"),
    ]

    class FakeBus:
        async def all_findings(self):
            return findings

    decision = await engine.evaluate(
        FakeBus(),
        "recon",
        AgentResult(status=AgentResultStatus.COMPLETE),
        _engagement(),
    )
    assert decision.rule
    assert decision.from_agent == "recon"
    assert decision.rationale
