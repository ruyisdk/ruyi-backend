import datetime

from fastapi import APIRouter
from sqlalchemy.sql.expression import select
from sqlalchemy.sql.expression import update

from ..cache import (
    DICacheStore,
    KEY_GITHUB_RELEASE_STATS,
    KEY_TELEMETRY_DATA_LAST_PROCESSED,
)
from ..components.frontend_dashboard_processor import crunch_and_cache_dashboard_numbers
from ..components.news_item_processor import refresh_news_items
from ..components.telemetry_processor import process_telemetry_data
from ..config.env import DIEnvConfig
from ..db.conn import DIMainDB
from ..db.schema import telemetry_raw_uploads, ModelTelemetryRawUpload
from ..es import DIMainES
from ..gh import DIGitHub
from ..schema.admin import ReqProcessTelemetry
from ..schema.client_telemetry import UploadPayload
from ..components.github_stats import query_release_downloads

router = APIRouter(prefix="/admin")


@router.post("/process-telemetry-v1", status_code=204)
async def admin_process_telemetry(
    req: ReqProcessTelemetry,
    main_db: DIMainDB,
    es: DIMainES,
    cache: DICacheStore,
) -> None:
    """Processes collected raw telemetry data so far."""

    async with main_db.connect() as conn:
        async with conn.begin() as txn:
            sel = select(
                telemetry_raw_uploads.c.id,
                telemetry_raw_uploads.c.raw_events,
            ).where(
                telemetry_raw_uploads.c.created_at >= req.time_start,
                telemetry_raw_uploads.c.created_at < req.time_end,
                telemetry_raw_uploads.c.is_processed == False,  # noqa: E712  # DSL usage
            )
            raw_events: list[ModelTelemetryRawUpload] = []
            upload_ids: list[int] = []
            async for row in await conn.stream(sel):
                upload_ids.append(row[0])
                raw_events.append(row[1])

            events = [UploadPayload.model_validate(x) for x in raw_events]

            # Process the telemetry data
            await process_telemetry_data(conn, events)

            # Mark the raw events as processed
            if upload_ids:
                upd = (
                    update(telemetry_raw_uploads)
                    .where(telemetry_raw_uploads.c.id.in_(upload_ids))
                    .values(is_processed=True)
                )
                await conn.execute(upd)

            # Commit the transaction
            await txn.commit()

    last_processed = datetime.datetime.now(datetime.timezone.utc)
    await cache.set(KEY_TELEMETRY_DATA_LAST_PROCESSED, last_processed)

    # refresh frontend dashboard numbers
    try:
        async with main_db.connect() as conn:
            await crunch_and_cache_dashboard_numbers(conn, es, cache)
    except Exception:
        pass


@router.post("/refresh-github-stats-v1", status_code=204)
async def admin_refresh_github_stats(
    cfg: DIEnvConfig,
    cache: DICacheStore,
    db: DIMainDB,
    es: DIMainES,
    github: DIGitHub,
) -> None:
    """Refreshes the cached GitHub stats."""

    stats = await query_release_downloads(github, cfg.github.ruyi_pm_repo)
    await cache.set(KEY_GITHUB_RELEASE_STATS, stats)

    # refresh frontend dashboard numbers
    try:
        async with db.connect() as conn:
            await crunch_and_cache_dashboard_numbers(conn, es, cache)
    except Exception:
        pass


@router.post("/refresh-repo-news-v1", status_code=204)
async def admin_refresh_repo_news(
    cfg: DIEnvConfig,
    cache: DICacheStore,
    github: DIGitHub,
) -> None:
    """Refreshes the cached RuyiSDK repository news items."""

    await refresh_news_items(github, cache, cfg.github.ruyi_packages_index_repo)
