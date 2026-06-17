import datetime
import json
from typing import Any, List, cast
from unittest.mock import AsyncMock

import pytest

from ruyi_backend.app.releases import (
    _generate_download_urls,
    _generate_ide_download_urls,
    _get_latest_releases,
)
from ruyi_backend.components.github_stats import (
    AssetDownloadStats,
    ReleaseDownloadStats,
    query_release_downloads,
)
from ruyi_backend.schema.releases import LatestReleasesV1

from .fixtures import RuyiFileFixtureFactory


@pytest.fixture
def release_stats(ruyi_file: RuyiFileFixtureFactory) -> List[ReleaseDownloadStats]:
    with ruyi_file.path("github-release-stats-cache.json") as p:
        with open(p, "r") as f:
            return cast(List[ReleaseDownloadStats], json.load(f))


def test_get_latest_releases(release_stats: List[ReleaseDownloadStats]) -> None:
    stats: List[ReleaseDownloadStats] = release_stats
    pm_repo = "foo/bar"
    result: LatestReleasesV1 = _get_latest_releases(
        stats, lambda s: _generate_download_urls(s, pm_repo)
    )
    channels = result.channels
    assert set(channels.keys()) == {"stable", "testing"}

    stable = channels["stable"]
    assert stable.version == "0.32.0"
    assert stable.channel == "stable"
    assert stable.release_date.isoformat() == "2025-04-21T23:35:47+00:00"
    assert stable.download_urls == {
        "linux/aarch64": [
            "https://github.com/foo/bar/releases/download/0.32.0/ruyi-0.32.0.arm64",
            "https://mirror.iscas.ac.cn/ruyisdk/ruyi/tags/0.32.0/ruyi-0.32.0.arm64",
        ],
        "linux/riscv64": [
            "https://github.com/foo/bar/releases/download/0.32.0/ruyi-0.32.0.riscv64",
            "https://mirror.iscas.ac.cn/ruyisdk/ruyi/tags/0.32.0/ruyi-0.32.0.riscv64",
        ],
        "linux/x86_64": [
            "https://github.com/foo/bar/releases/download/0.32.0/ruyi-0.32.0.amd64",
            "https://mirror.iscas.ac.cn/ruyisdk/ruyi/tags/0.32.0/ruyi-0.32.0.amd64",
        ],
    }

    testing = channels["testing"]
    assert testing.version == "0.32.0-beta.20250421"
    assert testing.channel == "testing"
    assert testing.release_date.isoformat() == "2025-04-21T14:33:33+00:00"
    assert testing.download_urls == {
        "linux/aarch64": [
            "https://github.com/foo/bar/releases/download/0.32.0-beta.20250421/ruyi-0.32.0-beta.20250421.arm64",
            "https://mirror.iscas.ac.cn/ruyisdk/ruyi/tags/0.32.0-beta.20250421/ruyi-0.32.0-beta.20250421.arm64",
        ],
        "linux/riscv64": [
            "https://github.com/foo/bar/releases/download/0.32.0-beta.20250421/ruyi-0.32.0-beta.20250421.riscv64",
            "https://mirror.iscas.ac.cn/ruyisdk/ruyi/tags/0.32.0-beta.20250421/ruyi-0.32.0-beta.20250421.riscv64",
        ],
        "linux/x86_64": [
            "https://github.com/foo/bar/releases/download/0.32.0-beta.20250421/ruyi-0.32.0-beta.20250421.amd64",
            "https://mirror.iscas.ac.cn/ruyisdk/ruyi/tags/0.32.0-beta.20250421/ruyi-0.32.0-beta.20250421.amd64",
        ],
    }


@pytest.fixture
def mock_github_client(ruyi_file: RuyiFileFixtureFactory) -> AsyncMock:
    """Create a mock GitHub client that returns fixture data."""
    mock_client = AsyncMock()

    # Load the fixture data for paginated responses
    responses: dict[str | None, Any] = {}
    for cursor in (None, "NTA"):
        with ruyi_file.path(f"github-release-query-graphql.{cursor or '0'}.json") as p:
            with open(p, "r") as f:
                responses[cursor] = json.load(f)

    # Configure the mock to return appropriate responses based on cursor
    async def mock_graphql(query: str, variables: dict[str, Any]) -> Any:
        cursor = variables.get("cursor")
        return responses[cursor]

    mock_client.async_graphql = AsyncMock(side_effect=mock_graphql)
    return mock_client


@pytest.mark.asyncio
async def test_query_release_downloads(mock_github_client: AsyncMock) -> None:
    """Test that query_release_downloads correctly processes paginated GitHub API responses."""

    # Call the function with mock client
    result = await query_release_downloads(mock_github_client, "ruyisdk/ruyi")

    # Verify the function made the expected GraphQL calls
    mock_github_client.async_graphql.assert_called()
    assert mock_github_client.async_graphql.call_count == 2

    # First call should use no cursor
    first_call = mock_github_client.async_graphql.call_args_list[0]
    assert first_call.kwargs["variables"]["owner"] == "ruyisdk"
    assert first_call.kwargs["variables"]["name"] == "ruyi"
    assert first_call.kwargs["variables"]["cursor"] is None

    # Second call should use the cursor from first page
    second_call = mock_github_client.async_graphql.call_args_list[1]
    assert second_call.kwargs["variables"]["cursor"] == "NTA"

    # Verify the result structure
    assert isinstance(result, list)
    assert len(result) == 77

    # Check a few specific entries to ensure data is correctly transformed
    # First release from the first fixture
    first_release = result[0]
    assert first_release["tag"] == "0.32.0"
    assert first_release["assets"][0]["name"] == "ruyi-0.32.0.tar.gz"
    assert first_release["assets"][0]["download_count"] == 5

    # Last release from the second fixture (found near the end of the combined list)
    last_release = next(r for r in result if r["tag"] == "0.2.0-beta.20231204")
    assert last_release["tag"] == "0.2.0-beta.20231204"
    assert "assets" in last_release
    assert len(last_release["assets"]) == 3  # This specific release has 3 assets


def make_ide_release_stats(
    tag: str,
    date: str,
    asset_names: list[str],
) -> ReleaseDownloadStats:
    return ReleaseDownloadStats(
        tag=tag,
        date=datetime.datetime.fromisoformat(date),
        assets=[
            AssetDownloadStats(name=name, download_count=0) for name in asset_names
        ],
    )


def test_generate_ide_download_urls_vscode() -> None:
    ide_repo = "ruyisdk/ruyisdk-vscode-extension"
    ide_slug = "vscode"
    release = make_ide_release_stats(
        "0.1.4",
        "2025-06-01T10:00:00+00:00",
        ["ruyisdk-vscode-extension-0.1.4.vsix"],
    )
    urls = _generate_ide_download_urls(release, ide_repo, ide_slug)
    assert urls == {
        "none/any": [
            "https://github.com/ruyisdk/ruyisdk-vscode-extension/releases/download/"
            "0.1.4/ruyisdk-vscode-extension-0.1.4.vsix",
            "https://mirror.iscas.ac.cn/ruyisdk/ide/plugins/vscode/"
            "0.1.4/ruyisdk-vscode-extension-0.1.4.vsix",
        ],
    }


def test_generate_ide_download_urls_eclipse() -> None:
    ide_repo = "ruyisdk/ruyisdk-eclipse-plugins"
    ide_slug = "eclipse"
    release = make_ide_release_stats(
        "0.1.4",
        "2025-06-01T10:00:00+00:00",
        ["ruyisdk-eclipse-plugins-0.1.4.zip"],
    )
    urls = _generate_ide_download_urls(release, ide_repo, ide_slug)
    assert urls == {
        "none/any": [
            "https://github.com/ruyisdk/ruyisdk-eclipse-plugins/releases/download/"
            "0.1.4/ruyisdk-eclipse-plugins-0.1.4.zip",
            "https://mirror.iscas.ac.cn/ruyisdk/ide/plugins/eclipse/"
            "0.1.4/ruyisdk-eclipse-plugins-0.1.4.zip",
        ],
    }


def test_generate_ide_download_urls_multiple_assets() -> None:
    ide_repo = "ruyisdk/ruyisdk-vscode-extension"
    ide_slug = "vscode"
    release = make_ide_release_stats(
        "0.1.4",
        "2025-06-01T10:00:00+00:00",
        [
            "ruyisdk-vscode-extension-0.1.4.vsix",
            "ruyisdk-vscode-extension-0.1.4.tar.gz",
        ],
    )
    urls = _generate_ide_download_urls(release, ide_repo, ide_slug)
    assert urls == {
        "none/any": [
            "https://github.com/ruyisdk/ruyisdk-vscode-extension/releases/download/"
            "0.1.4/ruyisdk-vscode-extension-0.1.4.vsix",
            "https://mirror.iscas.ac.cn/ruyisdk/ide/plugins/vscode/"
            "0.1.4/ruyisdk-vscode-extension-0.1.4.vsix",
            "https://github.com/ruyisdk/ruyisdk-vscode-extension/releases/download/"
            "0.1.4/ruyisdk-vscode-extension-0.1.4.tar.gz",
            "https://mirror.iscas.ac.cn/ruyisdk/ide/plugins/vscode/"
            "0.1.4/ruyisdk-vscode-extension-0.1.4.tar.gz",
        ],
    }


def test_get_latest_ide_releases() -> None:
    ide_repo = "ruyisdk/ruyisdk-vscode-extension"
    ide_slug = "vscode"
    stats = [
        make_ide_release_stats(
            "0.1.4",
            "2025-06-01T10:00:00+00:00",
            ["ruyisdk-vscode-extension-0.1.4.vsix"],
        ),
        make_ide_release_stats(
            "0.1.3",
            "2025-05-15T10:00:00+00:00",
            ["ruyisdk-vscode-extension-0.1.3.vsix"],
        ),
        make_ide_release_stats(
            "0.1.4-beta.1",
            "2025-05-30T10:00:00+00:00",
            ["ruyisdk-vscode-extension-0.1.4-beta.1.vsix"],
        ),
    ]
    result = _get_latest_releases(
        stats, lambda s: _generate_ide_download_urls(s, ide_repo, ide_slug)
    )
    channels = result.channels
    assert set(channels.keys()) == {"stable", "testing"}

    stable = channels["stable"]
    assert stable.version == "0.1.4"
    assert stable.channel == "stable"
    assert stable.download_urls == {
        "none/any": [
            "https://github.com/ruyisdk/ruyisdk-vscode-extension/releases/download/"
            "0.1.4/ruyisdk-vscode-extension-0.1.4.vsix",
            "https://mirror.iscas.ac.cn/ruyisdk/ide/plugins/vscode/"
            "0.1.4/ruyisdk-vscode-extension-0.1.4.vsix",
        ],
    }

    testing = channels["testing"]
    assert testing.version == "0.1.4-beta.1"
    assert testing.channel == "testing"
    assert testing.download_urls == {
        "none/any": [
            "https://github.com/ruyisdk/ruyisdk-vscode-extension/releases/download/"
            "0.1.4-beta.1/ruyisdk-vscode-extension-0.1.4-beta.1.vsix",
            "https://mirror.iscas.ac.cn/ruyisdk/ide/plugins/vscode/"
            "0.1.4-beta.1/ruyisdk-vscode-extension-0.1.4-beta.1.vsix",
        ],
    }
