from datetime import datetime, timedelta, timezone

import pytest

from spectre.bus.store import FindingsBus
from spectre.research.metrics import compute_metrics, export_session_metrics, handoffs_jsonl_lines
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import Finding, FindingStatus, FindingType, Severity


def _ts(base: datetime, seconds: float) -> datetime:
    return base + timedelta(seconds=seconds)


@pytest.mark.asyncio
async def test_compute_metrics_happy_path(tmp_path):
    base = datetime(2026, 6, 25, 12, 0, 0, tzinfo=timezone.utc)
    session_id = "eng_metrics"
    events = [
        BusEvent(
            type=EventType.ENGAGEMENT_STARTED,
            session_id=session_id,
            timestamp=base,
            payload={"repo": "tmestery/SPECTRE"},
        ),
        BusEvent(
            type=EventType.FINDING,
            session_id=session_id,
            timestamp=_ts(base, 5),
            payload={},
        ),
        BusEvent(
            type=EventType.HANDOFF_DECISION,
            session_id=session_id,
            timestamp=_ts(base, 10),
            payload={
                "rule": "repo_mapped",
                "from_agent": "recon",
                "to_agent": "vuln_hunter",
                "rationale": "mapped",
                "input_finding_ids": ["fnd_1"],
            },
        ),
        BusEvent(
            type=EventType.HANDOFF_DECISION,
            session_id=session_id,
            timestamp=_ts(base, 20),
            payload={
                "rule": "actionable_finding",
                "from_agent": "vuln_hunter",
                "to_agent": "exploiter",
                "rationale": "secret",
                "input_finding_ids": [],
            },
        ),
    ]
    findings = [
        Finding(
            type=FindingType.SECRET,
            agent="vuln_hunter",
            target="tmestery/SPECTRE:x",
            title="secret",
            severity=Severity.HIGH,
        ),
        Finding(
            type=FindingType.VALIDATION_ATTEMPT,
            agent="exploiter",
            target="tmestery/SPECTRE:x",
            title="validated",
            status=FindingStatus.CONFIRMED,
        ),
        Finding(
            type=FindingType.VALIDATION_ATTEMPT,
            agent="exploiter",
            target="tmestery/SPECTRE:y",
            title="fp",
            status=FindingStatus.FALSE_POSITIVE,
        ),
    ]

    metrics = compute_metrics(session_id, events, findings)
    assert metrics.time_to_first_finding_seconds == 5.0
    assert metrics.total_handoffs == 2
    assert metrics.handoff_counts_by_rule["repo_mapped"] == 1
    assert metrics.findings_per_agent["vuln_hunter"] == 1
    assert metrics.findings_per_agent["exploiter"] == 2
    assert metrics.false_positive_rate == 0.5
    assert metrics.time_to_handoff[0].seconds_from_start == 10.0

    bus = FindingsBus(tmp_path / session_id / "events.db")
    await bus.connect()
    try:
        await bus.publish(events[0])
        for finding in findings:
            await bus.publish(BusEvent.finding_event(session_id, finding))
        for event in events[2:]:
            await bus.publish(event)
        out = tmp_path / "out"
        exported = await export_session_metrics(bus, session_id, out)
        assert (out / "handoffs.jsonl").exists()
        assert (out / "metrics.json").exists()
        lines = (out / "handoffs.jsonl").read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        assert exported.total_handoffs == 2
        assert exported.false_positive_rate == 0.5
    finally:
        await bus.close()


def test_compute_metrics_empty_events_raises():
    with pytest.raises(ValueError, match="no events"):
        compute_metrics("eng_empty", [], [])


def test_compute_metrics_missing_started_raises():
    events = [
        BusEvent(
            type=EventType.FINDING,
            session_id="eng_x",
            payload={},
        )
    ]
    with pytest.raises(ValueError, match="no engagement_started"):
        compute_metrics("eng_x", events, [])


def test_compute_metrics_no_handoffs_and_no_validations():
    base = datetime(2026, 6, 25, 12, 0, 0, tzinfo=timezone.utc)
    events = [
        BusEvent(
            type=EventType.ENGAGEMENT_STARTED,
            session_id="eng_solo",
            timestamp=base,
            payload={},
        )
    ]
    metrics = compute_metrics("eng_solo", events, [])
    assert metrics.time_to_first_finding_seconds is None
    assert metrics.total_handoffs == 0
    assert metrics.false_positive_rate is None
    assert handoffs_jsonl_lines(events) == []
