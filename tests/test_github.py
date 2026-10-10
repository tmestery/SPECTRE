from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from spectre.bus.store import FindingsBus
from spectre.safety.scope import ScopeEnforcer, ScopeViolationError
from spectre.schemas.scope import RepoScope
from spectre.tools.github import GitHubClient


@pytest.fixture
async def bus(tmp_path):
    instance = FindingsBus(tmp_path / "s" / "events.db")
    await instance.connect()
    yield instance
    await instance.close()


def _response(payload, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=payload)
    return resp


@pytest.mark.asyncio
async def test_inventory_maps_repo(bus):
    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    client = GitHubClient(bus, "session", ScopeEnforcer(scope), token="")

    with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = [
            _response({"default_branch": "main", "description": "test", "html_url": "https://github.com/x"}),
            _response({"Python": 100}),
            _response([{"type": "file", "path": "README.md"}, {"type": "file", "path": "package.json"}]),
            _response({"workflows": [{"path": ".github/workflows/ci.yml"}]}),
        ]
        with patch.object(client, "_clone_repo", new=AsyncMock(return_value=None)):
            inventory = await client.inventory_repo("tmestery/SPECTRE", "main")

    assert inventory.repo == "tmestery/SPECTRE"
    assert "README.md" in inventory.files
    assert "package.json" in inventory.dependencies
    await client.close()


@pytest.mark.asyncio
async def test_rejects_out_of_scope_repo(bus):
    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    client = GitHubClient(bus, "session", ScopeEnforcer(scope))
    with pytest.raises(ScopeViolationError):
        await client.inventory_repo("octocat/Hello-World", "main")
    await client.close()


@pytest.mark.asyncio
async def test_api_failure_audited(bus):
    scope = RepoScope(name="t", allowed_repos=["tmestery/SPECTRE"])
    client = GitHubClient(bus, "session", ScopeEnforcer(scope))

    with patch.object(client._client, "get", new=AsyncMock(side_effect=RuntimeError("boom"))):
        with pytest.raises(RuntimeError):
            await client.inventory_repo("tmestery/SPECTRE", "main")

    await client.close()
