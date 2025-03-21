import datetime

from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql.expression import func, select

from ..db.schema import (
    telemetry_aggregated_events,
    telemetry_installation_infos,
)
from ..schema.frontend import DashboardDataV1, DashboardEventDetailV1


async def crunch_dashboard_numbers(
    db: AsyncConnection,
    es: AsyncElasticsearch,
) -> DashboardDataV1:
    """
    Ingests the semi-processed telemetry events to produce statistics for the
    RuyiSDK website dashboard.
    """

    # query download counts from ES
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    download_count_resp = await es.count(
        query={
            "bool": {
                "must": [
                    # only /ruyisdk/ruyi/ paths correspond to the RuyiSDK PM
                    {"wildcard": {"url.path": {"value": "/ruyisdk/ruyi/*"}}},
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
    download_count = download_count_resp["count"]

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

    return DashboardDataV1(
        downloads=DashboardEventDetailV1(total=download_count),
        installs=DashboardEventDetailV1(total=installation_count),
        top_packages={},  # TODO: numbers are not reported yet
        top_commands=top10_sorted_commands,
    )
