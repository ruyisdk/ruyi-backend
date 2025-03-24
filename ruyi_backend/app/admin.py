import datetime

from fastapi import APIRouter
from sqlalchemy.sql.expression import select
from sqlalchemy.sql.expression import update

from ..cache import DICacheStore, KEY_TELEMETRY_DATA_LAST_PROCESSED
from ..components.telemetry_processor import process_telemetry_data
from ..db.conn import DIMainDB
from ..db.schema import telemetry_raw_uploads, ModelTelemetryRawUpload
from ..schema.admin import ReqProcessTelemetry
from ..schema.client_telemetry import UploadPayload

router = APIRouter()


@router.post("/admin/process-telemetry-v1", status_code=204)
async def admin_process_telemetry(
    req: ReqProcessTelemetry,
    main_db: DIMainDB,
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
