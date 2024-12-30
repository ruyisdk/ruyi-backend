from fastapi import APIRouter

from ..db.conn import DIMainDB
from ..schema.client_telemetry import UploadPayload

router = APIRouter()


@router.post("/telemetry/pm/upload-v1", status_code=204)
async def telemetry_pm_upload_v1(payload: UploadPayload, main_db: DIMainDB) -> None:
    if payload.fmt != 1:
        raise ValueError("Invalid telemetry format version")

    async with main_db.connect() as conn:
        # TODO: de-dupe events with payload.nonce
        # TODO: record ruyi_version and installation info independently
        # TODO: record the aggregated events
        pass

    return None
