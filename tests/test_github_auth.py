import httpx

from spectre.github_auth import github_api_error_message, github_token_configured


def test_github_token_configured_false_when_empty(monkeypatch):
    monkeypatch.setattr("spectre.github_auth.settings.github_token", "")
    assert not github_token_configured()


def test_github_token_configured_true_when_set(monkeypatch):
    monkeypatch.setattr("spectre.github_auth.settings.github_token", "ghp_test")
    assert github_token_configured()


def test_github_api_error_message_for_404_without_token(monkeypatch):
    monkeypatch.setattr("spectre.github_auth.settings.github_token", "")
    request = httpx.Request("GET", "https://api.github.com/repos/tmestery/SPECTRE")
    response = httpx.Response(404, request=request)
    exc = httpx.HTTPStatusError("not found", request=request, response=response)
    message = github_api_error_message(exc, "tmestery/SPECTRE")
    assert message is not None
    assert "GITHUB_TOKEN" in message


def test_github_api_error_message_for_401(monkeypatch):
    monkeypatch.setattr("spectre.github_auth.settings.github_token", "bad")
    request = httpx.Request("GET", "https://api.github.com/repos/tmestery/SPECTRE")
    response = httpx.Response(401, request=request)
    exc = httpx.HTTPStatusError("unauthorized", request=request, response=response)
    message = github_api_error_message(exc, "tmestery/SPECTRE")
    assert message is not None
    assert "invalid or expired" in message
