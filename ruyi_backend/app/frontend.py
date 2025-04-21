from typing import cast

from fastapi import APIRouter

from ..cache import DICacheStore, KEY_FRONTEND_DASHBOARD
from ..db.conn import DIMainDB
from ..es import DIMainES
from ..schema.frontend import DashboardDataV1

router = APIRouter()


@router.post("/fe/dashboard")
async def get_dashboard_data_v1(
    main_db: DIMainDB,
    main_es: DIMainES,
    cache: DICacheStore,
) -> DashboardDataV1:
    # only consume cached results for performance
    return cast(DashboardDataV1, await cache.get(KEY_FRONTEND_DASHBOARD))
