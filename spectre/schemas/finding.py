from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class FindingType(str, Enum):
    REPOSITORY = "repository"
    BRANCH = "branch"
    FILE = "file"
    DEPENDENCY = "dependency"
    WORKFLOW = "workflow"
    SECRET = "secret"
    MISCONFIGURATION = "misconfiguration"
    VULNERABILITY = "vulnerability"
    VALIDATION_ATTEMPT = "validation_attempt"
    JUDGMENT = "judgment"
    NOTE = "note"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(str, Enum):
    TENTATIVE = "tentative"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    VALIDATED = "validated"


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: f"fnd_{uuid4().hex[:12]}")
    type: FindingType
    agent: str
    target: str
    severity: Severity = Severity.INFO
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    title: str
    description: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    related_ids: list[str] = Field(default_factory=list)
    handoff_hint: str | None = None
    status: FindingStatus = FindingStatus.TENTATIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return value
