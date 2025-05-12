import json
from typing import List, cast

import pytest

from ruyi_backend.app.releases import _get_latest_releases
from ruyi_backend.components.github_stats import ReleaseDownloadStats
from ruyi_backend.schema.releases import LatestReleasesV1

from .fixtures import RuyiFileFixtureFactory


@pytest.fixture
def release_stats(ruyi_file: RuyiFileFixtureFactory) -> List[ReleaseDownloadStats]:
    with ruyi_file.path("github-release-stats-cache.json") as p:
        with open(p, "r") as f:
            return cast(List[ReleaseDownloadStats], json.load(f))


def test_get_latest_releases(release_stats: List[ReleaseDownloadStats]) -> None:
    stats: List[ReleaseDownloadStats] = release_stats
    result: LatestReleasesV1 = _get_latest_releases(stats, "foo/bar")
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
