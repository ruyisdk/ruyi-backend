from fastapi import APIRouter

from ..components.frontend_dashboard_processor import crunch_dashboard_numbers
from ..db.conn import DIMainDB
from ..es import DIMainES
from ..schema.frontend import DashboardDataV1

router = APIRouter()


@router.post("/fe/dashboard")
async def get_dashboard_data_v1(
    main_db: DIMainDB,
    main_es: DIMainES,
) -> DashboardDataV1:
    # crunch the semi-processed numbers
    # TODO: put these into periodic background tasks and cache the result
    async with main_db.connect() as db:
        x = await crunch_dashboard_numbers(db, main_es)

    return x
