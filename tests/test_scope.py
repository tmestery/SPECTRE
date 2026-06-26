import pytest

from spectre.schemas.scope import RepoScope
from spectre.safety.scope import ScopeEnforcer, ScopeViolationError, redact_text


def test_allows_in_scope_repo():
    scope = RepoScope(name="test", allowed_repos=["tmestery/SPECTRE"])
    enforcer = ScopeEnforcer(scope)
    enforcer.check_repo("tmestery/SPECTRE")


def test_rejects_out_of_scope_repo():
    scope = RepoScope(name="test", allowed_repos=["tmestery/SPECTRE"])
    enforcer = ScopeEnforcer(scope)
    with pytest.raises(ScopeViolationError):
        enforcer.check_repo("octocat/Hello-World")


def test_rejects_invalid_branch():
    scope = RepoScope(name="test", allowed_repos=["tmestery/SPECTRE"], allowed_branches=["main"])
    enforcer = ScopeEnforcer(scope)
    with pytest.raises(ScopeViolationError):
        enforcer.check_branch("dev")


def test_excluded_path_not_allowed():
    scope = RepoScope(
        name="test",
        allowed_repos=["tmestery/SPECTRE"],
        exclude_paths=["node_modules/**"],
    )
    enforcer = ScopeEnforcer(scope)
    assert enforcer.check_path("src/main.py") is True
    assert enforcer.check_path("node_modules/pkg/index.js") is False


def test_redacts_secret_snippet():
    redacted = redact_text("key=AKIAIOSFODNN7EXAMPLE")
    assert "AKIA****" in redacted
    assert "EXAMPLE" not in redacted
