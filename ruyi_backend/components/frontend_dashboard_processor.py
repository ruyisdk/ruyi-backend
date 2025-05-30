from asyncio import gather
import datetime
from typing import cast

from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql.expression import func, select

from ..cache import (
    KEY_FRONTEND_DASHBOARD,
    KEY_GITHUB_RELEASE_STATS,
    KEY_TELEMETRY_DATA_LAST_PROCESSED,
)
from ..cache.store import CacheStore
from ..components.github_stats import ReleaseDownloadStats, merge_download_counts
from ..db.schema import (
    telemetry_aggregated_events,
    telemetry_installation_infos,
)
from ..schema.frontend import DashboardDataV1, DashboardEventDetailV1


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

    pm_gh_downloads = 0
    gh_stats: list[ReleaseDownloadStats] | None
    if gh_stats := await cache.get(KEY_GITHUB_RELEASE_STATS):
        pm_gh_downloads = merge_download_counts(gh_stats)

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

    # only /ruyisdk/ruyi/ paths correspond to the RuyiSDK PM
    pm_download_count = mirror_category_download_counts[4] + pm_gh_downloads
    pkg_download_count = mirror_category_download_counts[1]

    other_categories = {
        "3rdparty": DashboardEventDetailV1(total=mirror_category_download_counts[0]),
        "humans": DashboardEventDetailV1(total=mirror_category_download_counts[2]),
        "ide": DashboardEventDetailV1(total=mirror_category_download_counts[3]),
    }

    # count total installations
    installation_count = await db.scalar(
        select(func.count(1)).select_from(telemetry_installation_infos)
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
        downloads=DashboardEventDetailV1(total=pkg_download_count),
        pm_downloads=DashboardEventDetailV1(total=pm_download_count),
        other_categories_downloads=other_categories,
        installs=DashboardEventDetailV1(total=installation_count),
        top_packages={},  # TODO: numbers are not reported yet
        top_commands=top10_sorted_commands,
    )

    # cache the result
    try:
        await cache.set(KEY_FRONTEND_DASHBOARD, result.model_dump())
    except Exception:
        # ignore cache errors
        pass

    return result
