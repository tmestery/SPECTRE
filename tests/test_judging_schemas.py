import pytest
from pydantic import ValidationError

from spectre.schemas.events import EventType
from spectre.schemas.finding import FindingType
from spectre.schemas.judging import (
    HandoffVerdictPayload,
    JudgmentVerdict,
    ReportVerdictPayload,
    handoff_verdict_event,
    make_judgment_finding,
    report_verdict_event,
    validate_judgment_evidence,
)


def test_make_judgment_finding_happy_path():
    finding = make_judgment_finding(
        agent="finding_judge",
        target="tmestery/SPECTRE:secret",
        reviewed_finding_id="fnd_abc",
        verdict=JudgmentVerdict.UPHOLD,
        rationale="High-confidence AWS key pattern with file evidence.",
    )
    assert finding.type == FindingType.JUDGMENT
    assert finding.related_ids == ["fnd_abc"]
    assert finding.evidence["verdict"] == "uphold"
    assert validate_judgment_evidence(finding.evidence) == JudgmentVerdict.UPHOLD


def test_judgment_evidence_rejects_missing_reviewed_id():
    with pytest.raises(ValueError, match="reviewed_finding_id"):
        validate_judgment_evidence({"verdict": "uphold", "rationale": "ok"})


def test_handoff_verdict_rejects_non_advisory():
    with pytest.raises(ValidationError):
        HandoffVerdictPayload(
            decision_id="dec_1",
            verdict="approve",
            rationale="ok",
            advisory=False,
        )


def test_report_verdict_rejects_unknown_verdict():
    with pytest.raises(ValidationError):
        ReportVerdictPayload(verdict="ship_it", issues=[], advisory=True)


def test_verdict_event_factories():
    handoff = handoff_verdict_event(
        "eng_1",
        {
            "decision_id": "dec_1",
            "verdict": "defer",
            "rationale": "Need more evidence",
            "advisory": True,
        },
    )
    report = report_verdict_event(
        "eng_1",
        {
            "report_section_ids": ["sec_exec"],
            "verdict": "revise",
            "issues": ["Invented CVE path"],
            "advisory": True,
        },
    )
    assert handoff.type == EventType.HANDOFF_VERDICT
    assert handoff.payload["verdict"] == "defer"
    assert report.type == EventType.REPORT_VERDICT
    assert report.payload["issues"] == ["Invented CVE path"]
