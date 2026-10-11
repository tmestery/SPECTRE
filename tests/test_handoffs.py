import pytest

from spectre.orchestrator.handoffs import MAX_VALIDATION_FAILED_RETRIES, HandoffEngine
from spectre.schemas.engagement import AgentResult, AgentResultStatus, Engagement
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import Finding, FindingStatus, FindingType, Severity
from spectre.schemas.scope import RepoScope


def _engagement() -> Engagement:
    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    return Engagement(repo="tmestery/SPECTRE", branch="main", scope=scope)


class FakeBus:
    def __init__(
        self,
        findings: list[Finding] | None = None,
        events: list[BusEvent] | None = None,
    ) -> None:
        self._findings = findings or []
        self._events = events or []

    async def all_findings(self):
        return self._findings

    async def all_events(self, types=None):
        if types is None:
            return self._events
        allowed = {t.value for t in types}
        return [e for e in self._events if e.type.value in allowed]


@pytest.mark.asyncio
async def test_repo_mapped_handoff():
    engine = HandoffEngine(_engagement().scope)
    findings = [
        Finding(type=FindingType.REPOSITORY, agent="recon", target="tmestery/SPECTRE", title="repo"),
        Finding(type=FindingType.FILE, agent="recon", target="tmestery/SPECTRE:README.md", title="file"),
    ]

    decision = await engine.evaluate(
        FakeBus(findings),
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

    decision = await engine.evaluate(
        FakeBus(findings),
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

    decision = await engine.evaluate(
        FakeBus(findings),
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

    decision = await engine.evaluate(
        FakeBus(findings),
        "recon",
        AgentResult(status=AgentResultStatus.COMPLETE),
        _engagement(),
    )
    assert decision.rule
    assert decision.from_agent == "recon"
    assert decision.rationale


@pytest.mark.asyncio
async def test_validation_failed_retry_returns_to_vuln_hunter():
    engine = HandoffEngine(_engagement().scope)
    findings = [
        Finding(
            type=FindingType.SECRET,
            agent="vuln_hunter",
            target="tmestery/SPECTRE:a",
            title="secret",
            confidence=0.9,
            status=FindingStatus.TENTATIVE,
        ),
        Finding(
            type=FindingType.VALIDATION_ATTEMPT,
            agent="exploiter",
            target="tmestery/SPECTRE:a",
            title="fp",
            status=FindingStatus.FALSE_POSITIVE,
        ),
    ]
    decision = await engine.evaluate(
        FakeBus(findings),
        "exploiter",
        AgentResult(status=AgentResultStatus.COMPLETE),
        _engagement(),
    )
    assert decision.rule == "validation_failed_retry"
    assert decision.to_agent == "vuln_hunter"


@pytest.mark.asyncio
async def test_validation_failed_retry_stops_after_max():
    engine = HandoffEngine(_engagement().scope)
    findings = [
        Finding(
            type=FindingType.SECRET,
            agent="vuln_hunter",
            target="tmestery/SPECTRE:a",
            title="secret",
            confidence=0.9,
            status=FindingStatus.TENTATIVE,
        ),
        Finding(
            type=FindingType.VALIDATION_ATTEMPT,
            agent="exploiter",
            target="tmestery/SPECTRE:a",
            title="fp",
            status=FindingStatus.FALSE_POSITIVE,
            severity=Severity.HIGH,
        ),
    ]
    prior = [
        BusEvent(
            type=EventType.HANDOFF_DECISION,
            session_id="eng_x",
            payload={"rule": "validation_failed_retry"},
        )
        for _ in range(MAX_VALIDATION_FAILED_RETRIES)
    ]
    decision = await engine.evaluate(
        FakeBus(findings, prior),
        "exploiter",
        AgentResult(status=AgentResultStatus.EXHAUSTED),
        _engagement(),
    )
    assert decision.rule != "validation_failed_retry"
    assert decision.to_agent == "reporter"


@pytest.mark.asyncio
async def test_confirmed_validation_skips_retry():
    engine = HandoffEngine(_engagement().scope)
    findings = [
        Finding(
            type=FindingType.SECRET,
            agent="vuln_hunter",
            target="tmestery/SPECTRE:a",
            title="secret",
            confidence=0.9,
            status=FindingStatus.TENTATIVE,
        ),
        Finding(
            type=FindingType.VALIDATION_ATTEMPT,
            agent="exploiter",
            target="tmestery/SPECTRE:a",
            title="ok",
            status=FindingStatus.CONFIRMED,
        ),
    ]
    decision = await engine.evaluate(
        FakeBus(findings),
        "exploiter",
        AgentResult(status=AgentResultStatus.COMPLETE),
        _engagement(),
    )
    assert decision.rule == "finding_validated"
    assert decision.to_agent == "reporter"


@pytest.mark.asyncio
async def test_false_positive_without_pending_actionable_no_retry():
    engine = HandoffEngine(_engagement().scope)
    findings = [
        Finding(
            type=FindingType.VALIDATION_ATTEMPT,
            agent="exploiter",
            target="tmestery/SPECTRE:a",
            title="fp",
            status=FindingStatus.FALSE_POSITIVE,
        )
    ]
    decision = await engine.evaluate(
        FakeBus(findings),
        "exploiter",
        AgentResult(status=AgentResultStatus.COMPLETE),
        _engagement(),
    )
    assert decision.rule == "no_validation"
    assert decision.to_agent == "reporter"
