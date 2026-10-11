import httpx

from spectre.config import settings


def github_token_configured() -> bool:
    return bool(settings.github_token.strip())


def _is_github_api_error(exc: httpx.HTTPStatusError) -> bool:
    """Only map errors from api.github.com — not Groq/OpenAI/other HTTP 404s."""
    try:
        host = exc.request.url.host or ""
    except Exception:
        return False
    return host == "api.github.com" or host.endswith(".github.com")


def github_api_error_message(exc: BaseException, repo: str) -> str | None:
    if isinstance(exc, httpx.HTTPStatusError):
        if not _is_github_api_error(exc):
            return None
        status = exc.response.status_code
        if status == 401:
            return "GITHUB_TOKEN is invalid or expired. Update .env and restart the container."
        if status == 404:
            if not github_token_configured():
                return (
                    f"GitHub returned 404 for {repo}. Private repos require GITHUB_TOKEN in .env "
                    "(e.g. run: gh auth token)."
                )
            return (
                f"Repository not found or token lacks access to {repo}. "
                "Verify the repo slug and token scopes."
            )
        if status == 403:
            return f"GitHub API rate limit or forbidden access for {repo}."
    return None
