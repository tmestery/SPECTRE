"""Loadable handoff threshold profiles for research A/B experiments."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from spectre.config import settings
from spectre.schemas.finding import Severity


class HandoffProfile(BaseModel):
    name: str
    description: str = ""
    secret_confidence_min: float = Field(default=0.8, ge=0.0, le=1.0)
    vulnerability_exploitability_min: float = Field(default=0.7, ge=0.0, le=1.0)
    misconfiguration_severities: list[str] = Field(default_factory=lambda: ["high", "critical"])

    def misconfig_severity_set(self) -> set[Severity]:
        return {Severity(s) for s in self.misconfiguration_severities}


DEFAULT_PROFILE = HandoffProfile(name="default")


def profiles_dir() -> Path:
    return Path(settings.handoff_profiles_dir)


def load_handoff_profile(name: str | None = None) -> HandoffProfile:
    """Load a named profile from handoff_profiles/<name>.yaml."""
    if name is not None:
        profile_name = name.strip()
        if not profile_name:
            raise ValueError("handoff profile name is empty")
    else:
        profile_name = (settings.handoff_profile or "default").strip()
        if not profile_name:
            raise ValueError("handoff profile name is empty")

    path = profiles_dir() / f"{profile_name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"handoff profile not found: {profile_name} ({path})")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"handoff profile must be a mapping: {path}")
    data.setdefault("name", profile_name)
    profile = HandoffProfile.model_validate(data)
    # Validate severity enum values early
    profile.misconfig_severity_set()
    return profile
