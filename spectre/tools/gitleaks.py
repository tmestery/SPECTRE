import asyncio
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from spectre.bus.store import FindingsBus
from spectre.safety.audit import AuditTimer, audit_tool


@dataclass
class SecretMatch:
    file: str
    line: int
    rule: str
    match: str
    entropy: float = 0.0


FALLBACK_PATTERNS = [
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github-token", re.compile(r"ghp_[a-zA-Z0-9]{20,}")),
    ("generic-api-key", re.compile(r"(?i)(api[_-]?key|secret)\s*[:=]\s*['\"][^'\"]{8,}['\"]")),
]


class GitleaksScanner:
    def __init__(self, bus: FindingsBus, session_id: str) -> None:
        self.bus = bus
        self.session_id = session_id

    async def scan(self, workspace: Path, repo: str) -> list[SecretMatch]:
        if shutil.which("gitleaks"):
            return await self._scan_gitleaks(workspace, repo)
        return await self._scan_fallback(workspace, repo)

    async def _scan_gitleaks(self, workspace: Path, repo: str) -> list[SecretMatch]:
        timer = AuditTimer()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            report_path = tmp.name

        proc = await asyncio.create_subprocess_exec(
            "gitleaks",
            "detect",
            "--source",
            str(workspace),
            "--no-git",
            "--report-format",
            "json",
            "--report-path",
            report_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        exit_code = proc.returncode or 0
        await audit_tool(
            self.bus,
            self.session_id,
            tool="gitleaks",
            target=repo,
            scope_check="passed",
            exit_code=exit_code,
            duration_ms=timer.elapsed_ms(),
        )
        try:
            text = Path(report_path).read_text(encoding="utf-8").strip()
        finally:
            Path(report_path).unlink(missing_ok=True)

        if exit_code not in (0, 1):
            raise RuntimeError(stderr.decode().strip() or "gitleaks failed")
        if not text:
            return []
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return []

        matches: list[SecretMatch] = []
        for item in payload if isinstance(payload, list) else []:
            matches.append(
                SecretMatch(
                    file=item.get("File", ""),
                    line=int(item.get("StartLine") or 0),
                    rule=item.get("RuleID", "gitleaks"),
                    match=item.get("Secret", item.get("Match", "")),
                )
            )
        return matches

    async def _scan_fallback(self, workspace: Path, repo: str) -> list[SecretMatch]:
        timer = AuditTimer()
        matches: list[SecretMatch] = []
        for path in workspace.rglob("*"):
            if not path.is_file() or path.stat().st_size > 1_000_000:
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for line_no, line in enumerate(content.splitlines(), start=1):
                for rule, pattern in FALLBACK_PATTERNS:
                    found = pattern.search(line)
                    if found:
                        matches.append(
                            SecretMatch(
                                file=str(path.relative_to(workspace)),
                                line=line_no,
                                rule=rule,
                                match=found.group(0),
                            )
                        )
        await audit_tool(
            self.bus,
            self.session_id,
            tool="gitleaks_fallback",
            target=repo,
            scope_check="passed",
            exit_code=0,
            duration_ms=timer.elapsed_ms(),
            metadata={"matches": len(matches)},
        )
        return matches
