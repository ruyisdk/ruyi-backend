from typing import Final, cast

from fastapi import APIRouter

from ..cache import DICacheStore, KEY_GITHUB_RELEASE_STATS
from ..schema.releases import LatestReleasesV1, ReleaseDetailV1
import semver
from ..components.github_stats import ReleaseDownloadStats

router = APIRouter(prefix="/releases")

ARCH_NAME_DL_TO_UNAME = {
    "amd64": "x86_64",
    "arm64": "aarch64",
}

ARCH_NAME_UNAME_TO_DL: Final = {v: k for k, v in ARCH_NAME_DL_TO_UNAME.items()}


def get_supported_arches(release_stat: ReleaseDownloadStats) -> list[str]:
    """Returns the supported architectures for the given release."""

    # for now the release assets are named in the following manner:
    #
    # * source archive: ruyi-<version>.tar.gz
    # * onefile distributions: ruyi-<version>.<arch>
    #
    # with the <arch> currently coinciding with the Debian architecture names
    # (e.g. amd64 instead of x86_64, arm64 instead of aarch64).
    #
    # we can figure out the supported arches for the release this way
    arches = set()
    for asset in release_stat["assets"]:
        name = asset["name"]
        if name.endswith(".tar.gz"):
            # source archive
            continue
        arch_dl = name.rsplit(".", 1)[1]
        arches.add(ARCH_NAME_DL_TO_UNAME.get(arch_dl, arch_dl))
    return list(sorted(arches))


# Stub function for download URL generation
def _download_urls_for_one_asset(ver: str, channel: str, arch: str) -> list[str]:
    arch_dl = ARCH_NAME_UNAME_TO_DL.get(arch, arch)

    # TODO: make the list of mirrors customizable
    return [
        f"https://github.com/ruyisdk/ruyi/releases/download/{ver}/ruyi-{ver}.{arch_dl}",
        f"https://mirror.iscas.ac.cn/ruyisdk/ruyi/{channel}/{ver}/ruyi.{arch_dl}",
    ]


def _generate_download_urls(
    release_stat: ReleaseDownloadStats,
    channel: str,
) -> dict[str, list[str]]:
    """Generates download URLs for the given release."""

    # FIXME: we currently only provide Linux binaries, so the "linux" part is hardcoded
    # for now
    return {
        f"linux/{arch}": _download_urls_for_one_asset(
            release_stat["tag"], channel, arch
        )
        for arch in get_supported_arches(release_stat)
    }


def _get_latest_releases(
    stats: list[ReleaseDownloadStats],
) -> LatestReleasesV1:
    """Returns the latest releases for each channel."""

    latest_versions_by_channel: dict[str, semver.Version] = {}
    for rel in stats:
        tag = rel["tag"]
        try:
            v = semver.Version.parse(tag)
        except ValueError:
            continue
        channel = "testing" if v.prerelease else "stable"
        try:
            if v > latest_versions_by_channel[channel]:
                latest_versions_by_channel[channel] = v
        except KeyError:
            latest_versions_by_channel[channel] = v

    # now we have the latest version for each channel, let's build the response
    releases: dict[str, ReleaseDetailV1] = {}
    for channel, v in latest_versions_by_channel.items():
        release_stat: ReleaseDownloadStats | None = None
        for rel in stats:
            if rel["tag"] == str(v):
                release_stat = rel
                break
        assert release_stat is not None

        releases[channel] = ReleaseDetailV1(
            version=str(v),
            channel=channel,
            download_urls=_generate_download_urls(release_stat, channel),
        )
    return LatestReleasesV1(channels=releases)


@router.get("/latest-pm")
async def get_latest_pm_releases(
    cache: DICacheStore,
) -> LatestReleasesV1:
    # use the cached GitHub release stats as the data source
    stats = cast(list[ReleaseDownloadStats], await cache.get(KEY_GITHUB_RELEASE_STATS))
    return _get_latest_releases(stats)
