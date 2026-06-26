import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WorkflowIssue:
    path: str
    pattern: str
    severity: str
    description: str


WORKFLOW_PATTERNS = [
    (
        "pull_request_target",
        re.compile(r"pull_request_target\s*:"),
        "high",
        "Workflow uses pull_request_target which can be dangerous with untrusted code checkout",
    ),
    (
        "unpinned-action",
        re.compile(r"uses:\s*[^@\n]+@(v\d+|main|master)\b"),
        "medium",
        "Workflow uses loosely pinned action ref",
    ),
]


class WorkflowAnalyzer:
    def analyze_file(self, path: Path, workspace: Path) -> list[WorkflowIssue]:
        if not path.exists():
            return []
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return []

        rel = str(path.relative_to(workspace)) if path.is_relative_to(workspace) else str(path)
        issues: list[WorkflowIssue] = []
        for pattern_id, regex, severity, description in WORKFLOW_PATTERNS:
            if regex.search(content):
                issues.append(
                    WorkflowIssue(
                        path=rel,
                        pattern=pattern_id,
                        severity=severity,
                        description=description,
                    )
                )
        return issues

    def analyze_paths(self, workspace: Path, workflow_paths: list[str]) -> list[WorkflowIssue]:
        issues: list[WorkflowIssue] = []
        for rel_path in workflow_paths:
            issues.extend(self.analyze_file(workspace / rel_path, workspace))
        return issues
