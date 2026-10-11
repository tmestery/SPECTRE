"""Tests for loadable handoff threshold profiles (#37)."""

from pathlib import Path

import pytest

from spectre.orchestrator.handoffs import HandoffEngine
from spectre.orchestrator.profiles import load_handoff_profile
from spectre.research.metrics import compute_metrics
from spectre.schemas.engagement import AgentResult, AgentResultStatus, Engagement
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import Finding, FindingType
from spectre.schemas.scope import RepoScope


def _engagement(profile: str = "default") -> Engagement:
    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    return Engagement(
        repo="tmestery/SPECTRE",
        branch="main",
        scope=scope,
        handoff_profile=profile,
    )


class FakeBus:
    def __init__(self, findings: list[Finding] | None = None) -> None:
        self._findings = findings or []

    async def all_findings(self):
        return self._findings

    async def all_events(self, types=None):
        return []


@pytest.mark.asyncio
async def test_default_profile_handoffs_high_confidence_secret():
    profile = load_handoff_profile("default")
    engine = HandoffEngine(_engagement().scope, profile)
    findings = [
        Finding(
            type=FindingType.SECRET,
            agent="vuln_hunter",
            target="x",
            title="aws key",
            confidence=0.85,
        )
    ]
    decision = await engine.evaluate(
        FakeBus(findings),
        "vuln_hunter",
        AgentResult(status=AgentResultStatus.COMPLETE),
        _engagement(),
    )
    assert decision.rule == "actionable_finding"
    assert decision.to_agent == "exploiter"


@pytest.mark.asyncio
async def test_strict_profile_rejects_mid_confidence_secret():
    profile = load_handoff_profile("strict")
    engine = HandoffEngine(_engagement("strict").scope, profile)
    findings = [
        Finding(
            type=FindingType.SECRET,
            agent="vuln_hunter",
            target="x",
            title="maybe",
            confidence=0.85,
        )
    ]
    decision = await engine.evaluate(
        FakeBus(findings),
        "vuln_hunter",
        AgentResult(status=AgentResultStatus.EXHAUSTED),
        _engagement("strict"),
    )
    assert decision.to_agent == "reporter"
    assert decision.rule == "no_actionable_findings"


def test_missing_profile_raises():
    with pytest.raises(FileNotFoundError):
        load_handoff_profile("does-not-exist-xyz")


def test_empty_profile_name_raises():
    with pytest.raises(ValueError, match="empty"):
        load_handoff_profile("   ")


def test_invalid_profile_yaml_raises(tmp_path: Path, monkeypatch):
    bad = tmp_path / "broken.yaml"
    bad.write_text("- not a mapping\n", encoding="utf-8")
    monkeypatch.setattr(
        "spectre.orchestrator.profiles.settings.handoff_profiles_dir",
        tmp_path,
    )
    with pytest.raises(ValueError, match="mapping"):
        load_handoff_profile("broken")


def test_metrics_records_handoff_profile():
    started = BusEvent(
        type=EventType.ENGAGEMENT_STARTED,
        session_id="s1",
        payload={"handoff_profile": "strict"},
    )
    metrics = compute_metrics("s1", [started], [])
    assert metrics.handoff_profile == "strict"
