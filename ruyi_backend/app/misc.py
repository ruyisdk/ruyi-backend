from fastapi import APIRouter
from fastapi_health import health

router = APIRouter()


@router.get("/api-version")
async def api_version() -> dict[str, int]:
    return {"v": 1}


router.add_api_route("/health", endpoint=health([]))
