import asyncio
import os
import logging
import re
from typing import Any, NamedTuple, TypedDict, cast

import anyio
from githubkit import GitHub
from semver import Version

from ..config.env import ReleaseWorkerConfig
from ..gh import get_github

GITHUB_OWNER_REPO = "ruyisdk/ruyi"
RE_TARBALL_NAME = re.compile(r"\.tar(?:\.Z|\.gz|\.bz2|\.lz|\.lzma|\.xz|\.zst)?$")
RE_RUYI_RELEASE_ASSET_NAME = re.compile(
    r"^ruyi-(?P<ver>[0-9a-z.-]+)\.(?P<platform>[0-9a-z-]+)(?P<exe_suffix>\.exe)?$"
)


class GitHubReleaseAsset(TypedDict):
    url: str
    name: str
    size: int


class GitHubRelease(TypedDict):
    tag_name: str
    prerelease: bool
    assets: list[GitHubReleaseAsset]


class Release(NamedTuple):
    channel: str
    name: str


def transform_asset_name(name: str) -> str:
    if RE_TARBALL_NAME.search(name):
        return name
    m = RE_RUYI_RELEASE_ASSET_NAME.match(name)
    if not m:
        return name
    return f"ruyi.{m['platform']}{m['exe_suffix'] or ''}"


async def list_releases(gh: GitHub[Any], owner_repo: str) -> list[GitHubRelease]:
    resp = await gh.arequest(
        "GET",
        f"/repos/{owner_repo}/releases",
        params={"per_page": 3},
    )
    return cast(list[GitHubRelease], resp.json())


async def download_gh_release_asset_to(
    gh: GitHub[Any],
    asset: GitHubReleaseAsset,
    local: anyio.Path,
) -> None:
    resp = await gh.arequest(
        "GET",
        asset["url"],
        headers={"Accept": "application/octet-stream"},
    )
    await local.write_bytes(resp.content)
    mode = 0o755 if not RE_TARBALL_NAME.search(local.name) else 0o644
    await local.chmod(mode)


class Rsync:
    def __init__(
        self,
        logger: logging.Logger,
        conn_url: str,
        password: str | None = None,
    ) -> None:
        # ensure the remote URL does not end with a slash, because one is
        # to be appended at sync time
        self.conn_url = conn_url.rstrip("/")
        self.logger = logger
        self.password = password

    async def sync(self, rel: Release, local_dir: str | os.PathLike[Any]) -> None:
        new_env: dict[bytes, bytes] | None = None
        if self.password is not None:
            new_env = os.environb.copy()
            new_env[b"RSYNC_PASSWORD"] = self.password.encode("utf-8")

        remote_spec = f"{self.conn_url}/{rel.channel}/{rel.name}/"
        local_spec = f"{local_dir}/"

        args = ("-avHPL", "--exclude=.synced", local_spec, remote_spec)
        self.logger.info("calling rsync with args: %s", args[1:])
        process = await asyncio.create_subprocess_exec(
            "rsync",
            *args,
            env=new_env,
        )
        retcode = await process.wait()
        if retcode != 0:
            raise RuntimeError(f"rsync failed with code {retcode}")


class RsyncStagingDir:
    def __init__(self, local_dir: str) -> None:
        self.local_dir = anyio.Path(local_dir)

    def get_local_release_dir(self, rel: Release) -> anyio.Path:
        return self.local_dir / rel.channel / rel.name

    def get_marker_path_for_release(
        self,
        rel: Release,
        marker: str,
    ) -> anyio.Path:
        return self.get_local_release_dir(rel) / f".{marker}"

    async def is_release_synced(self, rel: Release) -> bool:
        return await self.get_marker_path_for_release(rel, "synced").exists()

    async def mark_release_synced(self, rel: Release) -> None:
        await self.get_marker_path_for_release(rel, "synced").touch()


class ReleaseSyncer:
    def __init__(self, cfg: ReleaseWorkerConfig) -> None:
        self.gh = get_github()
        self.logger = logging.getLogger("ruyi_backend.cli.cmd_sync_releases")

        rsync_dir = cfg.rsync_staging_dir
        rsync_url = cfg.rsync_remote_url
        rsync_pass = cfg.rsync_remote_pass or None

        if not rsync_dir:
            raise ValueError("rsync staging directory is not configured")
        if not rsync_url:
            raise ValueError("rsync remote URL is not configured")

        self.remote = Rsync(self.logger, rsync_url, rsync_pass)
        self.state_store = RsyncStagingDir(rsync_dir)

    async def ensure_release_assets(
        self,
        local_dir: anyio.Path,
        assets: list[GitHubReleaseAsset],
    ) -> None:
        for asset in assets:
            name = asset["name"]
            local_file = local_dir / name
            self.logger.debug("asset %s: local %s", name, local_file)
            try:
                if (await local_file.stat()).st_size == asset["size"]:
                    self.logger.debug("asset %s: size matches", name)
                    continue
            except FileNotFoundError:
                pass
            self.logger.info("removing %s", local_file)
            await local_file.unlink(missing_ok=True)
            await download_gh_release_asset_to(self.gh, asset, local_file)
            filemode = (
                0o755 if RE_TARBALL_NAME.search(local_file.name) is None else 0o644
            )
            await local_file.chmod(filemode)

            # make compat symlink for the onefile distribution assets
            # previously the assets at the RuyiSDK mirror were named without
            # the version number, but we prefer the GitHub Release asset names
            # now so downstream doesn't need to adapt to 2 different naming
            # conventions
            local_file_symlink = local_dir / transform_asset_name(name)
            await local_file_symlink.symlink_to(local_file.name)

    async def run(self) -> int:
        self.logger.info("rsync staging directory at %s", self.state_store.local_dir)

        releases = await list_releases(self.gh, GITHUB_OWNER_REPO)
        tasks = [self.run_one(gh_rel) for gh_rel in releases]
        await asyncio.gather(*tasks)
        return 0

    async def run_one(self, gh_rel: GitHubRelease) -> None:
        name = gh_rel["tag_name"]

        ver = Version.parse(name)
        # skip previous releases that were manually managed
        if ver <= Version.parse("0.6.0"):
            self.logger.debug("%s: ignoring pre-automation releases", name)
            return

        # consider both the GitHub release metadata and the semver when determining
        # the appropriate release channel
        channel = "testing" if gh_rel["prerelease"] or ver.prerelease else "stable"
        rel = Release(channel, name)

        is_synced = await self.state_store.is_release_synced(rel)
        synced_str = "synced" if is_synced else "needs sync"
        self.logger.info("%s: %s %s", name, channel, synced_str)
        if is_synced:
            return

        rel_dir = self.state_store.get_local_release_dir(rel)
        await rel_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info("%s: pulling assets", name)
        await self.ensure_release_assets(rel_dir, gh_rel["assets"])

        self.logger.info("%s: pushing to remote", name)
        await self.remote.sync(rel, rel_dir)
        await self.state_store.mark_release_synced(rel)


async def do_sync_releases(cfg: ReleaseWorkerConfig) -> int:
    syncer = ReleaseSyncer(cfg)
    return await syncer.run()
