from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from spectre.safety.scope import redact_text
from spectre.schemas.events import BusEvent, EventType
from spectre.schemas.finding import Finding, FindingStatus, FindingType, Severity
from spectre.schemas.scope import RepoScope

SECURITY_TYPES = {
    FindingType.SECRET,
    FindingType.VULNERABILITY,
    FindingType.MISCONFIGURATION,
    FindingType.VALIDATION_ATTEMPT,
}


@dataclass
class ReportSection:
    id: str
    title: str
    markdown: str


class ReportGenerator:
    def __init__(self, repo: str, branch: str, scope: RepoScope) -> None:
        self.repo = repo
        self.branch = branch
        self.scope = scope
        self.sections: list[ReportSection] = []

    def github_permalink(self, file_path: str, line: int | None = None) -> str:
        normalized = file_path.lstrip("/")
        url = f"https://github.com/{self.repo}/blob/{self.branch}/{normalized}"
        if line:
            return f"{url}#L{line}"
        return url

    def _file_from_target(self, target: str) -> tuple[str, int | None]:
        if ":" not in target:
            return target, None
        _, path = target.split(":", 1)
        if "#" in path:
            file_path, line_str = path.rsplit("#", 1)
            try:
                return file_path, int(line_str)
            except ValueError:
                return path, None
        return path, None

    def _dedupe_findings(self, findings: list[Finding]) -> list[Finding]:
        seen: set[tuple[str, str, str]] = set()
        unique: list[Finding] = []
        for finding in findings:
            key = (finding.type.value, finding.target, finding.title)
            if key in seen:
                continue
            seen.add(key)
            unique.append(finding)
        return unique

    def _security_findings(self, findings: list[Finding]) -> list[Finding]:
        deduped = self._dedupe_findings(findings)
        return [
            f
            for f in deduped
            if f.type in SECURITY_TYPES
            and f.status != FindingStatus.FALSE_POSITIVE
            and f.severity != Severity.INFO
        ]

    def _handoff_lines(self, events: list[BusEvent]) -> list[str]:
        lines: list[str] = []
        for event in events:
            if event.type != EventType.HANDOFF_DECISION:
                continue
            payload = event.payload
            from_agent = payload.get("from_agent", "?")
            to_agent = payload.get("to_agent") or "(end)"
            rule = payload.get("rule", "?")
            rationale = payload.get("rationale", "")
            lines.append(f"- **{from_agent} → {to_agent}** (`{rule}`): {rationale}")
        return lines

    def _evidence_line(self, finding: Finding) -> str:
        file_path = finding.evidence.get("file") or finding.evidence.get("path")
        line = finding.evidence.get("line")
        if not file_path:
            file_path, line = self._file_from_target(finding.target)
        if file_path:
            link = self.github_permalink(file_path, line if isinstance(line, int) else None)
            loc = f"{file_path}:{line}" if line else file_path
            return f"**Location:** [{loc}]({link})"
        return f"**Target:** {finding.target}"

    def _snippet_line(self, finding: Finding) -> str | None:
        snippet = finding.evidence.get("snippet_redacted")
        if not snippet:
            return None
        return f"**Evidence:** `{redact_text(str(snippet))}`"

    def build_sections(
        self,
        findings: list[Finding],
        events: list[BusEvent],
        *,
        executive_summary: str | None = None,
    ) -> list[ReportSection]:
        self.sections = []
        scanned_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        security = self._security_findings(findings)
        confirmed = [f for f in security if f.status == FindingStatus.CONFIRMED]
        high_or_above = [f for f in security if f.severity in {Severity.HIGH, Severity.CRITICAL}]

        summary_lines = [
            f"**Target:** `{self.repo}` @ `{self.branch}`",
            f"**Scanned:** {scanned_at}",
            f"**Scope:** {self.scope.name}",
            "",
            f"- Security findings: **{len(security)}**",
            f"- Confirmed validations: **{len(confirmed)}**",
            f"- High/Critical: **{len(high_or_above)}**",
        ]
        if executive_summary:
            summary_lines.extend(["", executive_summary])
        summary_md = "\n".join(summary_lines)
        self.sections.append(ReportSection("executive_summary", "Executive Summary", summary_md))

        scope_md = "\n".join(
            [
                f"- Allowed repos: {', '.join(f'`{r}`' for r in self.scope.allowed_repos)}",
                f"- Allowed branches: {', '.join(f'`{b}`' for b in self.scope.allowed_branches)}",
                f"- Authorization: {self.scope.authorization}",
            ]
        )
        self.sections.append(ReportSection("scope", "Scope", scope_md))

        if security:
            table_rows = [
                "| ID | Severity | Type | Location | Status |",
                "| --- | --- | --- | --- | --- |",
            ]
            for finding in security:
                file_path, _ = self._file_from_target(finding.target)
                if finding.evidence.get("file"):
                    file_path = str(finding.evidence["file"])
                link = self.github_permalink(file_path) if file_path else finding.target
                table_rows.append(
                    f"| {finding.id} | {finding.severity.value} | {finding.type.value} "
                    f"| [{file_path or finding.target}]({link}) | {finding.status.value} |"
                )
            self.sections.append(
                ReportSection("findings_summary", "Findings Summary", "\n".join(table_rows))
            )

            detail_blocks: list[str] = []
            for finding in security:
                block = [f"### {finding.id}: {finding.title}", self._evidence_line(finding)]
                snippet = self._snippet_line(finding)
                if snippet:
                    block.append(snippet)
                if finding.description:
                    block.append(finding.description)
                detail_blocks.append("\n".join(block))
            self.sections.append(
                ReportSection("detailed_findings", "Detailed Findings", "\n\n".join(detail_blocks))
            )
        else:
            self.sections.append(
                ReportSection(
                    "findings_summary",
                    "Findings Summary",
                    "No security findings above info severity.",
                )
            )

        handoffs = self._handoff_lines(events)
        coordination = "\n".join(handoffs) if handoffs else "No handoff decisions recorded."
        self.sections.append(ReportSection("coordination_log", "Agent Coordination Log", coordination))

        priority: list[str] = []
        if any(f.type == FindingType.SECRET for f in security):
            priority.append("1. Rotate exposed credentials and purge from git history")
        if any(f.type == FindingType.VULNERABILITY for f in security):
            priority.append("2. Patch vulnerable dependencies")
        if any(f.type == FindingType.MISCONFIGURATION for f in security):
            priority.append("3. Fix workflow and CI misconfigurations")
        if not priority:
            priority.append("1. No critical remediation items identified")
        self.sections.append(
            ReportSection("remediation", "Remediation Priority", "\n".join(f"- {p}" for p in priority))
        )

        return self.sections

    def render_markdown(
        self,
        findings: list[Finding],
        events: list[BusEvent],
        *,
        executive_summary: str | None = None,
    ) -> str:
        sections = self.build_sections(findings, events, executive_summary=executive_summary)
        parts = ["# SPECTRE Repository Security Report", ""]
        for section in sections:
            parts.append(f"## {section.title}")
            parts.append("")
            parts.append(section.markdown)
            parts.append("")
        return "\n".join(parts).rstrip() + "\n"

    def render_html(self, markdown: str) -> str:
        body_lines: list[str] = []
        for line in markdown.splitlines():
            if line.startswith("# "):
                body_lines.append(f"<h1>{escape(line[2:])}</h1>")
            elif line.startswith("## "):
                body_lines.append(f"<h2>{escape(line[3:])}</h2>")
            elif line.startswith("### "):
                body_lines.append(f"<h3>{escape(line[4:])}</h3>")
            elif line.startswith("|"):
                body_lines.append(line)
            elif not line.strip():
                body_lines.append("<br/>")
            else:
                body_lines.append(f"<p>{escape(line)}</p>")
        body = "\n".join(body_lines)
        return (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<title>SPECTRE Report</title>"
            "<style>body{font-family:ui-monospace,monospace;background:#0b0f14;color:#d8e1ea;"
            "padding:2rem;max-width:960px;margin:0 auto}h1,h2,h3{color:#7dd3fc}"
            "a{color:#38bdf8}table{border-collapse:collapse;width:100%}td,th{border:1px solid #334155;padding:.5rem}"
            "</style></head><body>"
            f"{body}</body></html>"
        )

    def write_reports(self, session_id: str, markdown: str, reports_dir: Path | None = None) -> tuple[Path, Path]:
        out_dir = reports_dir or Path("reports")
        out_dir.mkdir(parents=True, exist_ok=True)
        md_path = out_dir / f"{session_id}.md"
        html_path = out_dir / f"{session_id}.html"
        md_path.write_text(markdown, encoding="utf-8")
        html_path.write_text(self.render_html(markdown), encoding="utf-8")
        return md_path, html_path
