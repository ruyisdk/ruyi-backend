from asyncio import gather
import datetime
import sys
import traceback
from typing import cast

from elasticsearch import AsyncElasticsearch
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql.expression import func, select

from ..cache import (
    KEY_FRONTEND_DASHBOARD,
    KEY_GITHUB_ORG_STATS_RUYISDK,
    KEY_GITHUB_RELEASE_STATS,
    KEY_GITHUB_RELEASE_STATS_RUYI_IDE_ECLIPSE,
    KEY_PYPI_DOWNLOAD_TOTAL_PM,
    KEY_TELEMETRY_DATA_LAST_PROCESSED,
)
from ..cache.store import CacheStore
from ..components.github_stats import (
    GitHubOrgStats,
    ReleaseDownloadStats,
    merge_download_counts,
)
from ..db.schema import (
    telemetry_aggregated_events,
    telemetry_installation_infos,
)
from ..schema.frontend import (
    DashboardDataV1,
    DashboardEventDetailV1,
    DashboardGitHubOrgStatsV1,
    DashboardGitHubRepoStatsV1,
)


async def crunch_and_cache_dashboard_numbers(
    db: AsyncConnection,
    es: AsyncElasticsearch,
    cache: CacheStore,
) -> DashboardDataV1:
    """
    Ingests the semi-processed telemetry events to produce statistics for the
    RuyiSDK website dashboard, refreshing the cache.
    """

    try:
        last_updated = await cache.get(KEY_TELEMETRY_DATA_LAST_PROCESSED)
        if not isinstance(last_updated, datetime.datetime):
            # malformed cache entry
            raise ValueError()
    except Exception:
        # graceful degrade to something sensible
        last_updated = datetime.datetime.now(datetime.timezone.utc)

    gh_org_stats: list[DashboardGitHubOrgStatsV1] = []
    if cached_gh_org_stats_ruyisdk := await cache.get(KEY_GITHUB_ORG_STATS_RUYISDK):
        try:
            gh_org_stats_ruyisdk = GitHubOrgStats.model_validate(
                cached_gh_org_stats_ruyisdk
            )
            gh_org_stats.append(_github_org_stats_for_dashboard(gh_org_stats_ruyisdk))
        except ValidationError:
            # ignore malformed cache entries
            pass

    pm_gh_downloads = 0
    gh_stats: list[ReleaseDownloadStats] | None
    if gh_stats := await cache.get(KEY_GITHUB_RELEASE_STATS):
        pm_gh_downloads = merge_download_counts(gh_stats)

    ide_eclipse_gh_downloads = 0
    gh_stats_ide_eclipse: list[ReleaseDownloadStats] | None
    if gh_stats_ide_eclipse := await cache.get(
        KEY_GITHUB_RELEASE_STATS_RUYI_IDE_ECLIPSE
    ):
        ide_eclipse_gh_downloads = merge_download_counts(gh_stats_ide_eclipse)

    pm_pypi_downloads = await cache.get(KEY_PYPI_DOWNLOAD_TOTAL_PM) or 0

    # query download counts from ES
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    async def query_es_count(path: str) -> int:
        resp = await es.count(
            query={
                "bool": {
                    "must": [
                        {"wildcard": {"url.path": {"value": path}}},
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": "2025-01-01T00:00:00+08:00",
                                    "lt": now.isoformat(),
                                }
                            }
                        },
                    ]
                }
            }
        )
        return cast(int, resp["count"])

    mirror_category_download_counts = await gather(
        query_es_count("/ruyisdk/3rdparty/*"),
        query_es_count("/ruyisdk/dist/*"),
        query_es_count("/ruyisdk/humans/*"),
        query_es_count("/ruyisdk/ide/*"),
        query_es_count("/ruyisdk/ruyi/*"),
    )

    categories = {
        # only /ruyisdk/ruyi/ paths correspond to the RuyiSDK PM
        "pkg": DashboardEventDetailV1(total=mirror_category_download_counts[1]),
        "pm:github": DashboardEventDetailV1(total=pm_gh_downloads),
        "pm:mirror": DashboardEventDetailV1(total=mirror_category_download_counts[4]),
        "pm:pypi": DashboardEventDetailV1(total=pm_pypi_downloads),
        "3rdparty": DashboardEventDetailV1(total=mirror_category_download_counts[0]),
        "humans": DashboardEventDetailV1(total=mirror_category_download_counts[2]),
        "ide:eclipse:mirror": DashboardEventDetailV1(
            total=mirror_category_download_counts[3],
        ),
        "ide:eclipse:github": DashboardEventDetailV1(total=ide_eclipse_gh_downloads),
    }

    # compatibility response field
    pm_downloads = DashboardEventDetailV1(
        total=sum(v.total for k, v in categories.items() if k.startswith("pm:")),
    )
    ide_downloads = DashboardEventDetailV1(
        total=sum(v.total for k, v in categories.items() if k.startswith("ide:")),
    )
    other_categories = categories.copy()
    keys_to_remove = []
    for k in other_categories:
        if k.startswith("pm:") or k.startswith("ide:") or k == "pkg":
            keys_to_remove.append(k)
    for k in keys_to_remove:
        del other_categories[k]
    other_categories["ide"] = ide_downloads

    # count total installations
    installation_count = await db.scalar(
        select(func.count(1)).select_from(telemetry_installation_infos),
    )

    # count invocations grouped by individual ruyi commands
    command_counts: dict[str, int] = {}
    async for ev in await db.stream(
        select(
            telemetry_aggregated_events.c.params_kv_raw,
            telemetry_aggregated_events.c.count,
        ).where(
            telemetry_aggregated_events.c.kind == "cli:invocation-v1",
        ),
    ):
        kv = {k: v for k, v in ev[0]}  # [["key", "xxx"], ] => {"key": "xxx"}
        count = ev[1]

        cmd = kv.get("key")
        if cmd is None:
            continue

        cmd = "ruyi" if cmd == "<bare>" else f"ruyi {cmd}"
        command_counts[cmd] = command_counts.get(cmd, 0) + count

    sorted_command_counts = dict(
        sorted(
            command_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )
    )

    top10_sorted_commands = {
        k: DashboardEventDetailV1(total=v)
        for k, v in list(sorted_command_counts.items())[:10]
    }

    result = DashboardDataV1(
        last_updated=last_updated,
        downloads=categories["pkg"],
        pm_downloads=pm_downloads,
        other_categories_downloads=other_categories,
        downloads_by_categories_v1=categories,
        installs=DashboardEventDetailV1(total=installation_count),
        top_packages={},  # TODO: numbers are not reported yet
        top_commands=top10_sorted_commands,
        github_org_stats=gh_org_stats,
    )

    # cache the result
    try:
        await cache.set(KEY_FRONTEND_DASHBOARD, result.model_dump())
    except Exception as e:
        # ignore cache errors
        traceback.print_exception(e, file=sys.stderr)
        print("Failed to cache dashboard data; ignoring", file=sys.stderr)

    return result


def _github_org_stats_for_dashboard(
    stats: GitHubOrgStats,
) -> DashboardGitHubOrgStatsV1:
    return DashboardGitHubOrgStatsV1(
        name=stats.name,
        watchers_count=stats.watchers_count,
        forks_count=stats.forks_count,
        stars_count=stats.stars_count,
        prs_count=stats.prs_count,
        issues_count=stats.issues_count,
        contributors_count=stats.contributors_count,
        detail_by_repo=[
            DashboardGitHubRepoStatsV1(
                name=r.name,
                watchers_count=r.watchers_count,
                forks_count=r.forks_count,
                stars_count=r.stars_count,
                prs_count=r.prs_count,
                issues_count=r.issues_count,
                contributors_count=len(r.contributors),
            )
            for r in stats.detail_by_repo
        ],
    )
