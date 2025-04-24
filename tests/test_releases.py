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
    result: LatestReleasesV1 = _get_latest_releases(stats)
    channels = result.channels
    assert set(channels.keys()) == {"stable", "testing"}

    stable = channels["stable"]
    assert stable.version == "0.31.0"
    assert stable.channel == "stable"
    assert stable.download_urls == {
        "linux/aarch64": [
            "https://github.com/ruyisdk/ruyi/releases/download/0.31.0/ruyi-0.31.0.arm64",
            "https://mirror.iscas.ac.cn/ruyisdk/ruyi/tags/0.31.0/ruyi-0.31.0.arm64",
        ],
        "linux/riscv64": [
            "https://github.com/ruyisdk/ruyi/releases/download/0.31.0/ruyi-0.31.0.riscv64",
            "https://mirror.iscas.ac.cn/ruyisdk/ruyi/tags/0.31.0/ruyi-0.31.0.riscv64",
        ],
        "linux/x86_64": [
            "https://github.com/ruyisdk/ruyi/releases/download/0.31.0/ruyi-0.31.0.amd64",
            "https://mirror.iscas.ac.cn/ruyisdk/ruyi/tags/0.31.0/ruyi-0.31.0.amd64",
        ],
    }

    testing = channels["testing"]
    assert testing.version == "0.32.0-alpha.20250409"
    assert testing.channel == "testing"
    assert testing.download_urls == {
        "linux/aarch64": [
            "https://github.com/ruyisdk/ruyi/releases/download/0.32.0-alpha.20250409/ruyi-0.32.0-alpha.20250409.arm64",
            "https://mirror.iscas.ac.cn/ruyisdk/ruyi/tags/0.32.0-alpha.20250409/ruyi-0.32.0-alpha.20250409.arm64",
        ],
        "linux/riscv64": [
            "https://github.com/ruyisdk/ruyi/releases/download/0.32.0-alpha.20250409/ruyi-0.32.0-alpha.20250409.riscv64",
            "https://mirror.iscas.ac.cn/ruyisdk/ruyi/tags/0.32.0-alpha.20250409/ruyi-0.32.0-alpha.20250409.riscv64",
        ],
        "linux/x86_64": [
            "https://github.com/ruyisdk/ruyi/releases/download/0.32.0-alpha.20250409/ruyi-0.32.0-alpha.20250409.amd64",
            "https://mirror.iscas.ac.cn/ruyisdk/ruyi/tags/0.32.0-alpha.20250409/ruyi-0.32.0-alpha.20250409.amd64",
        ],
    }
