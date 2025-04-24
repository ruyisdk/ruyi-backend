from fastapi import APIRouter
from sqlalchemy import text

from ..db.conn import DIMainDB
from ..schema.client_telemetry import UploadPayload

router = APIRouter(prefix="/telemetry")


@router.post("/pm/upload-v1", status_code=204)
async def telemetry_pm_upload_v1(payload: UploadPayload, main_db: DIMainDB) -> None:
    if payload.fmt != 1:
        raise ValueError("Invalid telemetry format version")

    async with main_db.connect() as conn:
        # Record payload.ruyi_version into telemetry_ruyi_versions
        await conn.execute(
            text("INSERT INTO `telemetry_ruyi_versions` (version) VALUES (:version)"),
            {"version": payload.ruyi_version},
        )

        # Record payload.installation into telemetry_raw_installation_infos
        if ins := payload.installation:
            await conn.execute(
                text(
                    "INSERT IGNORE INTO `telemetry_raw_installation_infos` (`report_uuid`, `raw`) VALUES (:report_uuid, :raw)"
                ),
                {
                    "report_uuid": ins.report_uuid,
                    "raw": ins.model_dump_json(),
                },
            )

        # Record the raw aggregated events into telemetry_raw_uploads
        # De-duping is achieved by using INSERT IGNORE INTO and the unique
        # constraint on the nonce column
        await conn.execute(
            text(
                "INSERT IGNORE INTO `telemetry_raw_uploads` (`nonce`, `raw_events`) VALUES (:nonce, :raw_events)"
            ),
            {
                "nonce": payload.nonce,
                "raw_events": payload.model_dump_json(),
            },
        )

        await conn.commit()

    return None
