"""Tests for vuln-sample scope and planted demo fixtures (#13)."""

from pathlib import Path

import pytest

from spectre.safety.scope import ScopeEnforcer, ScopeViolationError
from spectre.schemas.scope import RepoScope
from spectre.tools.gitleaks import FALLBACK_PATTERNS
from spectre.tools.workflows import WorkflowAnalyzer

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "vuln-sample"
SCOPE_PATH = Path(__file__).resolve().parents[1] / "scopes" / "vuln-sample.yaml"


def test_vuln_sample_scope_allows_sample_repo():
    scope = RepoScope.load(SCOPE_PATH)
    enforcer = ScopeEnforcer(scope)
    enforcer.check_repo("tmestery/spectre-vuln-sample")
    assert scope.allows_branch("main")


def test_vuln_sample_scope_rejects_other_repos():
    scope = RepoScope.load(SCOPE_PATH)
    enforcer = ScopeEnforcer(scope)
    with pytest.raises(ScopeViolationError):
        enforcer.check_repo("tmestery/SPECTRE")


def test_vuln_sample_scope_rejects_wrong_branch():
    scope = RepoScope.load(SCOPE_PATH)
    enforcer = ScopeEnforcer(scope)
    with pytest.raises(ScopeViolationError):
        enforcer.check_branch("develop")


def test_fixture_planted_aws_key_matches_fallback():
    content = (FIXTURE_ROOT / "src" / "config.js").read_text(encoding="utf-8")
    aws_rule = next(p for rid, p in FALLBACK_PATTERNS if rid == "aws-access-key")
    assert aws_rule.search(content), "planted AWS key should match fallback scanner"


def test_fixture_workflow_flags_pull_request_target():
    analyzer = WorkflowAnalyzer()
    issues = analyzer.analyze_file(
        FIXTURE_ROOT / ".github" / "workflows" / "pr-target.yml",
        FIXTURE_ROOT,
    )
    assert any(i.pattern == "pull_request_target" for i in issues)
