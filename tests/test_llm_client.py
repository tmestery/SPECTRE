import pytest

from spectre.llm.client import LLMClient, MockLLMClient
from spectre.llm.json_utils import extract_json_object


def test_extract_json_object_from_fenced_block():
    data = extract_json_object('```json\n{"summary":"ok"}\n```')
    assert data["summary"] == "ok"


def test_llm_client_unavailable_without_api_key(monkeypatch):
    monkeypatch.setattr("spectre.config.settings.groq_api_key", "")
    monkeypatch.setattr("spectre.config.settings.llm_enabled", True)
    client = LLMClient.from_settings()
    assert not client.available


@pytest.mark.asyncio
async def test_mock_llm_returns_json_for_surface_prompt():
    client = MockLLMClient()
    from spectre.llm.types import LLMMessage

    result = await client.complete(
        [LLMMessage(role="user", content="attack surface analysis")],
        json_mode=True,
    )
    data = extract_json_object(result.content)
    assert "summary" in data


@pytest.mark.asyncio
async def test_mock_llm_complete_without_json_mode():
    client = MockLLMClient()
    from spectre.llm.types import LLMMessage

    result = await client.complete([LLMMessage(role="user", content="hello")])
    assert result.content


def test_llm_client_available_with_key(monkeypatch):
    monkeypatch.setattr("spectre.config.settings.groq_api_key", "gsk_test")
    monkeypatch.setattr("spectre.config.settings.llm_enabled", True)
    client = LLMClient.from_settings()
    assert client.available
