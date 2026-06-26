from spectre.agents.cognitive import finding_to_context
from spectre.schemas.finding import Finding, FindingType


def findings_by_types(findings: list[Finding], types: set[FindingType]) -> list[dict]:
    return [finding_to_context(f) for f in findings if f.type in types]
