"""Coordination metrics and handoff JSONL export for research analysis."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from spectre.bus.store import FindingsBus
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import FindingStatus, FindingType


@dataclass
class HandoffTiming:
    rule: str
    from_agent: str
    to_agent: str | None
    seconds_from_start: float
    input_finding_ids: list[str] = field(default_factory=list)


@dataclass
class CoordinationMetrics:
    session_id: str
    time_to_first_finding_seconds: float | None
    time_to_handoff: list[HandoffTiming]
    findings_per_agent: dict[str, int]
    false_positive_rate: float | None
    handoff_counts_by_rule: dict[str, int]
    validation_confirmed: int
    validation_false_positive: int
    total_findings: int
    total_handoffs: int

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data


def _event_seconds(event: BusEvent, start: datetime) -> float:
    ts = event.timestamp
    if ts.tzinfo is None:
        start_naive = start.replace(tzinfo=None) if start.tzinfo else start
        return (ts - start_naive).total_seconds()
    if start.tzinfo is None:
        return (ts.replace(tzinfo=None) - start).total_seconds()
    return (ts - start).total_seconds()


def compute_metrics(session_id: str, events: list[BusEvent], findings: list) -> CoordinationMetrics:
    """Compute coordination metrics from bus events and findings.

    Raises ValueError when the session has no engagement_started event.
    """
    if not events:
        raise ValueError(f"no events for session: {session_id}")

    started = next((e for e in events if e.type == EventType.ENGAGEMENT_STARTED), None)
    if started is None:
        raise ValueError(f"no engagement_started event for session: {session_id}")

    start_ts = started.timestamp
    finding_events = [e for e in events if e.type == EventType.FINDING]
    time_to_first: float | None = None
    if finding_events:
        time_to_first = _event_seconds(finding_events[0], start_ts)

    handoff_timings: list[HandoffTiming] = []
    rule_counts: Counter[str] = Counter()
    for event in events:
        if event.type != EventType.HANDOFF_DECISION:
            continue
        payload = event.payload
        rule = str(payload.get("rule", "unknown"))
        rule_counts[rule] += 1
        handoff_timings.append(
            HandoffTiming(
                rule=rule,
                from_agent=str(payload.get("from_agent", "")),
                to_agent=payload.get("to_agent"),
                seconds_from_start=_event_seconds(event, start_ts),
                input_finding_ids=list(payload.get("input_finding_ids") or []),
            )
        )

    per_agent: Counter[str] = Counter(f.agent for f in findings)

    confirmed = sum(
        1
        for f in findings
        if f.type == FindingType.VALIDATION_ATTEMPT and f.status == FindingStatus.CONFIRMED
    )
    false_pos = sum(
        1
        for f in findings
        if f.type == FindingType.VALIDATION_ATTEMPT and f.status == FindingStatus.FALSE_POSITIVE
    )
    denom = confirmed + false_pos
    fp_rate: float | None = (false_pos / denom) if denom > 0 else None

    return CoordinationMetrics(
        session_id=session_id,
        time_to_first_finding_seconds=time_to_first,
        time_to_handoff=handoff_timings,
        findings_per_agent=dict(sorted(per_agent.items())),
        false_positive_rate=fp_rate,
        handoff_counts_by_rule=dict(sorted(rule_counts.items())),
        validation_confirmed=confirmed,
        validation_false_positive=false_pos,
        total_findings=len(findings),
        total_handoffs=len(handoff_timings),
    )


def handoffs_jsonl_lines(events: list[BusEvent]) -> list[str]:
    lines: list[str] = []
    for event in events:
        if event.type != EventType.HANDOFF_DECISION:
            continue
        record = {
            "id": event.id,
            "session_id": event.session_id,
            "sequence_num": event.sequence_num,
            "timestamp": event.timestamp.isoformat(),
            **event.payload,
        }
        lines.append(json.dumps(record, default=str))
    return lines


async def export_session_metrics(
    bus: FindingsBus,
    session_id: str,
    session_dir: Path,
) -> CoordinationMetrics:
    """Write handoffs.jsonl + metrics.json under session_dir; return metrics."""
    events = await bus.all_events()
    findings = await bus.all_findings()
    metrics = compute_metrics(session_id, events, findings)

    session_dir.mkdir(parents=True, exist_ok=True)
    handoffs_path = session_dir / "handoffs.jsonl"
    metrics_path = session_dir / "metrics.json"

    lines = handoffs_jsonl_lines(events)
    handoffs_path.write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8")
    metrics_path.write_text(
        json.dumps(metrics.to_dict(), indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return metrics
