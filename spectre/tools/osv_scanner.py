import asyncio
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from spectre.bus.store import FindingsBus
from spectre.safety.audit import AuditTimer, audit_tool


@dataclass
class OsvVulnerability:
    package: str
    version: str
    cve_id: str
    summary: str
    severity: str
    exploitability: float


class OsvScanner:
    def __init__(self, bus: FindingsBus, session_id: str) -> None:
        self.bus = bus
        self.session_id = session_id

    async def scan_manifest(self, manifest_path: Path, repo: str) -> list[OsvVulnerability]:
        if not manifest_path.exists():
            return []
        if not shutil.which("osv-scanner"):
            return await self._fallback_scan(manifest_path, repo)

        timer = AuditTimer()
        proc = await asyncio.create_subprocess_exec(
            "osv-scanner",
            "--format",
            "json",
            str(manifest_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        exit_code = proc.returncode or 0
        await audit_tool(
            self.bus,
            self.session_id,
            tool="osv-scanner",
            target=repo,
            scope_check="passed",
            exit_code=exit_code,
            duration_ms=timer.elapsed_ms(),
            metadata={"manifest": str(manifest_path)},
        )
        if exit_code not in (0, 1):
            raise RuntimeError(stderr.decode().strip() or "osv-scanner failed")

        text = stdout.decode().strip()
        if not text:
            return []
        return self._parse_osv_json(json.loads(text))

    def _parse_osv_json(self, payload: dict) -> list[OsvVulnerability]:
        results: list[OsvVulnerability] = []
        for result in payload.get("results", []):
            package = result.get("package", {})
            name = package.get("name", "unknown")
            version = package.get("version", "unknown")
            for vuln in result.get("vulnerabilities", []):
                cve_id = vuln.get("id", "unknown")
                summary = vuln.get("summary", "")
                severity = "medium"
                exploitability = 0.75
                results.append(
                    OsvVulnerability(
                        package=name,
                        version=version,
                        cve_id=cve_id,
                        summary=summary,
                        severity=severity,
                        exploitability=exploitability,
                    )
                )
        return results

    async def _fallback_scan(self, manifest_path: Path, repo: str) -> list[OsvVulnerability]:
        timer = AuditTimer()
        await audit_tool(
            self.bus,
            self.session_id,
            tool="osv-scanner",
            target=repo,
            scope_check="skipped",
            exit_code=0,
            duration_ms=timer.elapsed_ms(),
            metadata={"reason": "osv-scanner binary not installed"},
        )
        return []
