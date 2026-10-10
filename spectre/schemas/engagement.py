from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from spectre.schemas.scope import RepoScope


class EngagementStatus(str, Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    HALTED = "halted"
    COMPLETE = "complete"
    FAILED = "failed"


class Engagement(BaseModel):
    id: str = Field(default_factory=lambda: f"eng_{uuid4().hex[:12]}")
    repo: str
    branch: str = "main"
    scope: RepoScope
    status: EngagementStatus = EngagementStatus.INITIALIZING
    halt_requested: bool = False
    workspace_path: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    max_duration_minutes: int = 30


class AgentResultStatus(str, Enum):
    COMPLETE = "complete"
    BLOCKED = "blocked"
    EXHAUSTED = "exhausted"


class AgentResult(BaseModel):
    status: AgentResultStatus
    message: str = ""
    iterations_used: int = 0


class EngagementResult(BaseModel):
    engagement_id: str
    status: EngagementStatus
    findings_count: int = 0
    message: str = ""
