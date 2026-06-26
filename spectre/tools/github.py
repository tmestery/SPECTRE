import asyncio
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from spectre.bus.store import FindingsBus
from spectre.config import settings
from spectre.github_auth import github_api_error_message
from spectre.safety.audit import AuditTimer, audit_tool
from spectre.safety.scope import ScopeEnforcer, ScopeViolationError

DEPENDENCY_MANIFESTS = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "Pipfile",
    "Pipfile.lock",
    "pyproject.toml",
    "go.mod",
    "Cargo.toml",
}


@dataclass
class RepoInventory:
    repo: str
    branch: str
    default_branch: str
    languages: dict[str, int] = field(default_factory=dict)
    files: list[str] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    clone_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class GitHubClient:
    def __init__(
        self,
        bus: FindingsBus,
        session_id: str,
        enforcer: ScopeEnforcer,
        token: str | None = None,
    ) -> None:
        self.bus = bus
        self.session_id = session_id
        self.enforcer = enforcer
        self.token = token or settings.github_token or None
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self._client = httpx.AsyncClient(base_url="https://api.github.com", headers=headers, timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def inventory_repo(self, repo: str, branch: str) -> RepoInventory:
        self.enforcer.check_repo(repo)
        self.enforcer.check_branch(branch)

        timer = AuditTimer()
        try:
            repo_resp = await self._client.get(f"/repos/{repo}")
            if repo_resp.is_error:
                self._raise_github_api_error(repo_resp, repo)

            repo_data = repo_resp.json()

            languages_resp = await self._client.get(f"/repos/{repo}/languages")
            if languages_resp.is_error:
                self._raise_github_api_error(languages_resp, repo)
            languages = languages_resp.json()

            contents = await self._walk_contents(repo, "")
            workflows = await self._list_workflows(repo)
            dependencies = [path for path in contents if Path(path).name in DEPENDENCY_MANIFESTS]
            clone_path = await self._clone_repo(repo, branch)

            inventory = RepoInventory(
                repo=repo,
                branch=branch,
                default_branch=repo_data.get("default_branch", branch),
                languages=languages,
                files=contents,
                workflows=workflows,
                dependencies=dependencies,
                clone_path=clone_path,
                metadata={
                    "description": repo_data.get("description"),
                    "private": repo_data.get("private"),
                    "html_url": repo_data.get("html_url"),
                },
            )
        except Exception as exc:
            await audit_tool(
                self.bus,
                self.session_id,
                tool="github_api",
                target=repo,
                scope_check="failed",
                exit_code=1,
                duration_ms=timer.elapsed_ms(),
                metadata={"error": str(exc)},
            )
            friendly = github_api_error_message(exc, repo)
            if friendly:
                raise RuntimeError(friendly) from exc
            raise

        await audit_tool(
            self.bus,
            self.session_id,
            tool="github_api",
            target=repo,
            scope_check="passed",
            exit_code=0,
            duration_ms=timer.elapsed_ms(),
            metadata={"files": len(inventory.files), "workflows": len(inventory.workflows)},
        )
        return inventory

    async def _walk_contents(self, repo: str, path: str) -> list[str]:
        files: list[str] = []
        response = await self._client.get(f"/repos/{repo}/contents/{path}")
        if response.status_code == 404:
            return files
        response.raise_for_status()
        entries = response.json()
        if not isinstance(entries, list):
            return files

        for entry in entries:
            entry_path = entry["path"]
            if entry["type"] == "dir":
                if not self.enforcer.check_path(entry_path):
                    continue
                files.extend(await self._walk_contents(repo, entry_path))
            else:
                if self.enforcer.check_path(entry_path):
                    files.append(entry_path)
        return sorted(files)

    async def _list_workflows(self, repo: str) -> list[str]:
        response = await self._client.get(f"/repos/{repo}/actions/workflows")
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
        return [item["path"] for item in data.get("workflows", [])]

    async def _clone_repo(self, repo: str, branch: str) -> Path | None:
        if shutil.which("git") is None:
            return None

        timer = AuditTimer()
        temp_dir = Path(tempfile.mkdtemp(prefix="spectre-clone-"))
        url = f"https://github.com/{repo}.git"
        if self.token:
            url = f"https://x-access-token:{self.token}@github.com/{repo}.git"

        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            branch,
            url,
            str(temp_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        exit_code = proc.returncode or 0

        await audit_tool(
            self.bus,
            self.session_id,
            tool="git_clone",
            target=repo,
            scope_check="passed",
            exit_code=exit_code,
            duration_ms=timer.elapsed_ms(),
            metadata={"branch": branch},
        )

        if exit_code != 0:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(stderr.decode().strip() or "git clone failed")

        return temp_dir

    def _raise_github_api_error(self, response: httpx.Response, repo: str) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            friendly = github_api_error_message(exc, repo)
            if friendly:
                raise RuntimeError(friendly) from exc
            raise


__all__ = ["DEPENDENCY_MANIFESTS", "GitHubClient", "RepoInventory", "ScopeViolationError"]
