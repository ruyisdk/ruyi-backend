from collections.abc import Callable
from typing import Final, cast

from fastapi import APIRouter, Response
import semver

from ..cache import (
    DICacheStore,
    KEY_GITHUB_RELEASE_STATS,
    KEY_GITHUB_RELEASE_STATS_RUYI_IDE_ECLIPSE,
    KEY_GITHUB_RELEASE_STATS_RUYI_IDE_VSCODE,
)
from ..config.env import DIEnvConfig
from ..components.github_stats import ReleaseDownloadStats
from ..components.news_items import NEWS_ITEM_NOT_FOUND, get_news_item_markdown
from ..schema.releases import LatestReleasesV1, ReleaseDetailV1

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


def get_dl_mirrors(pm_repo: str) -> list[str]:
    """Returns a list of download mirrors."""

    # TODO: make the list of mirrors customizable
    return [
        f"https://github.com/{pm_repo}/releases/download/",
        "https://mirror.iscas.ac.cn/ruyisdk/ruyi/tags/",
    ]


# Stub function for download URL generation
def _download_urls_for_one_asset(
    ver: str,
    arch: str,
    pm_repo: str,
) -> list[str]:
    arch_dl = ARCH_NAME_UNAME_TO_DL.get(arch, arch)
    return [base + f"{ver}/ruyi-{ver}.{arch_dl}" for base in get_dl_mirrors(pm_repo)]


def _generate_download_urls(
    s: ReleaseDownloadStats,
    pm_repo: str,
) -> dict[str, list[str]]:
    """Generates download URLs for the given release."""

    # FIXME: we currently only provide Linux binaries, so the "linux" part is hardcoded
    # for now
    return {
        f"linux/{arch}": _download_urls_for_one_asset(s["tag"], arch, pm_repo)
        for arch in get_supported_arches(s)
    }


def _get_ide_dl_mirrors(ide_repo: str, ide_slug: str) -> list[str]:
    """Returns a list of download mirrors for an IDE plugin. They are format
    strings ready to get interpolated."""

    return [
        f"https://github.com/{ide_repo}/releases/download/{{tag}}/{{name}}",
        # plugin are currently stored without a tag directory in the ISCAS mirror layout
        f"https://mirror.iscas.ac.cn/ruyisdk/ide/plugins/{ide_slug}/{{name}}",
    ]


def _generate_ide_download_urls(
    s: ReleaseDownloadStats,
    ide_repo: str,
    ide_slug: str,
) -> dict[str, list[str]]:
    """Generates download URLs for an IDE plugin release."""

    tag = s["tag"]
    mirrors = _get_ide_dl_mirrors(ide_repo, ide_slug)
    urls: list[str] = []
    for asset in s["assets"]:
        urls.extend(base.format(tag=tag, name=asset["name"]) for base in mirrors)
    return {"none/any": urls}


def _get_latest_releases(
    stats: list[ReleaseDownloadStats],
    url_generator: Callable[[ReleaseDownloadStats], dict[str, list[str]]],
) -> LatestReleasesV1:
    """Returns the latest releases for each channel."""

    latest_versions_by_channel: dict[str, semver.Version] = {}
    for rel in stats:
        tag = rel["tag"]
        semver_str = tag[1:] if tag.startswith("v") else tag
        try:
            v = semver.Version.parse(semver_str)
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
        ver_str = str(v)
        for rel in stats:
            tag = rel["tag"]
            if tag == ver_str or tag == f"v{ver_str}":
                release_stat = rel
                break
        assert release_stat is not None

        releases[channel] = ReleaseDetailV1(
            version=ver_str,
            channel=channel,
            release_date=release_stat["date"],
            download_urls=url_generator(release_stat),
        )
    return LatestReleasesV1(channels=releases)


@router.get("/latest-pm")
async def get_latest_pm_releases(
    cfg: DIEnvConfig,
    cache: DICacheStore,
) -> LatestReleasesV1:
    # use the cached GitHub release stats as the data source
    stats = cast(list[ReleaseDownloadStats], await cache.get(KEY_GITHUB_RELEASE_STATS))
    pm_repo = cfg.github.ruyi_pm_repo
    return _get_latest_releases(stats, lambda s: _generate_download_urls(s, pm_repo))


@router.get("/latest-ide/vscode")
async def get_latest_ide_vscode_releases(
    cfg: DIEnvConfig,
    cache: DICacheStore,
) -> LatestReleasesV1:
    stats = cast(
        list[ReleaseDownloadStats],
        await cache.get(KEY_GITHUB_RELEASE_STATS_RUYI_IDE_VSCODE),
    )
    ide_repo = cfg.github.ruyi_ide_vscode_repo
    return _get_latest_releases(
        stats, lambda s: _generate_ide_download_urls(s, ide_repo, "vscode")
    )


@router.get("/latest-ide/eclipse")
async def get_latest_ide_eclipse_releases(
    cfg: DIEnvConfig,
    cache: DICacheStore,
) -> LatestReleasesV1:
    stats = cast(
        list[ReleaseDownloadStats],
        await cache.get(KEY_GITHUB_RELEASE_STATS_RUYI_IDE_ECLIPSE),
    )
    ide_repo = cfg.github.ruyi_ide_eclipse_repo
    return _get_latest_releases(
        stats, lambda s: _generate_ide_download_urls(s, ide_repo, "eclipse")
    )


@router.get("/changelog/news/{tag}.json")
async def get_news_changelog(
    tag: str,
    cache: DICacheStore,
    response: Response,
) -> dict[str, str]:
    """Returns the changelog news item for the given tag if present."""

    try:
        sv = semver.Version.parse(tag)
    except ValueError:
        response.status_code = 404
        return NEWS_ITEM_NOT_FOUND

    # by convention RuyiSDK x.y.0 is called "x.y" in news item IDs
    version_str = f"{sv.major}.{sv.minor}" if sv.patch == 0 else str(sv)
    content = await get_news_item_markdown(f"ruyi-{version_str}", cache)
    if not content:
        response.status_code = 404
        return NEWS_ITEM_NOT_FOUND

    return content
