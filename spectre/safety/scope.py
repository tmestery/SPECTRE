import fnmatch
import re

from spectre.schemas.scope import RepoScope


class ScopeViolationError(Exception):
    pass


class ScopeEnforcer:
    def __init__(self, scope: RepoScope) -> None:
        self.scope = scope

    def check_repo(self, slug: str) -> None:
        if not self.scope.allows_repo(slug):
            raise ScopeViolationError(f"repo not in scope: {slug}")

    def check_branch(self, branch: str) -> None:
        if not self.scope.allows_branch(branch):
            raise ScopeViolationError(f"branch not in scope: {branch}")

    def check_path(self, path: str) -> bool:
        normalized = path.lstrip("./")
        for pattern in self.scope.exclude_paths:
            if fnmatch.fnmatch(normalized, pattern):
                return False
        for pattern in self.scope.include_paths:
            if fnmatch.fnmatch(normalized, pattern):
                return True
        return False


SECRET_PATTERNS = [
    re.compile(r"(AKIA[0-9A-Z]{16})"),
    re.compile(r"(ghp_[a-zA-Z0-9]{20,})"),
    re.compile(r"(sk-[a-zA-Z0-9]{20,})"),
]


def redact_text(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda m: m.group(1)[:4] + "****", redacted)
    return redacted


def redact_evidence(evidence: dict) -> dict:
    result = {}
    for key, value in evidence.items():
        if isinstance(value, str):
            result[key] = redact_text(value)
        else:
            result[key] = value
    return result
