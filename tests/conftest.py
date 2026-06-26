import pytest

import spectre.agents.cognitive as cognitive_module
from spectre.config import settings


@pytest.fixture(autouse=True)
def disable_llm_for_unit_tests(monkeypatch):
    """Keep unit tests deterministic unless they inject MockLLMClient explicitly."""
    monkeypatch.setattr(settings, "llm_enabled", False)
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "openai_api_key", "")
    cognitive_module._runtime = None
    yield
    cognitive_module._runtime = None
