"""Schemas and helpers for advisory judging-layer verdicts."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import Finding, FindingType, Severity


class JudgmentVerdict(str, Enum):
    UPHOLD = "uphold"
    DOWNGRADE = "downgrade"
    DISMISS = "dismiss"


class HandoffVerdictValue(str, Enum):
    APPROVE = "approve"
    DEFER = "defer"
    REJECT = "reject"


class ReportVerdictValue(str, Enum):
    ACCEPT = "accept"
    REVISE = "revise"


class HandoffVerdictPayload(BaseModel):
    decision_id: str
    verdict: HandoffVerdictValue
    rationale: str
    advisory: bool = True

    @field_validator("advisory")
    @classmethod
    def advisory_must_be_true_v1(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("handoff_verdict.advisory must be true in v1")
        return value


class ReportVerdictPayload(BaseModel):
    report_section_ids: list[str] = Field(default_factory=list)
    verdict: ReportVerdictValue
    issues: list[str] = Field(default_factory=list)
    rationale: str = ""
    advisory: bool = True

    @field_validator("advisory")
    @classmethod
    def advisory_must_be_true_v1(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("report_verdict.advisory must be true in v1")
        return value


def make_judgment_finding(
    *,
    agent: str,
    target: str,
    reviewed_finding_id: str,
    verdict: JudgmentVerdict | str,
    rationale: str,
    title: str | None = None,
    severity: Severity = Severity.INFO,
) -> Finding:
    """Build a judgment finding with required evidence fields."""
    verdict_value = JudgmentVerdict(verdict)
    return Finding(
        type=FindingType.JUDGMENT,
        agent=agent,
        target=target,
        severity=severity,
        title=title or f"Judgment: {verdict_value.value}",
        description=rationale,
        evidence={
            "verdict": verdict_value.value,
            "rationale": rationale,
            "reviewed_finding_id": reviewed_finding_id,
        },
        related_ids=[reviewed_finding_id],
    )


def validate_judgment_evidence(evidence: dict[str, Any]) -> JudgmentVerdict:
    if "verdict" not in evidence:
        raise ValueError("judgment evidence requires verdict")
    if "reviewed_finding_id" not in evidence or not evidence["reviewed_finding_id"]:
        raise ValueError("judgment evidence requires reviewed_finding_id")
    if "rationale" not in evidence:
        raise ValueError("judgment evidence requires rationale")
    return JudgmentVerdict(evidence["verdict"])


def handoff_verdict_event(session_id: str, payload: HandoffVerdictPayload | dict) -> BusEvent:
    model = (
        payload
        if isinstance(payload, HandoffVerdictPayload)
        else HandoffVerdictPayload.model_validate(payload)
    )
    return BusEvent(
        type=EventType.HANDOFF_VERDICT,
        session_id=session_id,
        payload=model.model_dump(mode="json"),
    )


def report_verdict_event(session_id: str, payload: ReportVerdictPayload | dict) -> BusEvent:
    model = (
        payload
        if isinstance(payload, ReportVerdictPayload)
        else ReportVerdictPayload.model_validate(payload)
    )
    return BusEvent(
        type=EventType.REPORT_VERDICT,
        session_id=session_id,
        payload=model.model_dump(mode="json"),
    )
