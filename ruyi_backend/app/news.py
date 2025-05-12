import json

from fastapi import APIRouter, Response

from ..cache import DICacheStore
from ..components.news_items import get_news_item_markdown

router = APIRouter(prefix="/news")


@router.get("/get/{item_id}.json")
async def get_news_item_markdown_v1(
    item_id: str,
    cache: DICacheStore,
) -> Response:
    """Returns the news item in Markdown format."""

    item = await get_news_item_markdown(item_id, cache)
    if not item:
        return Response("news item not found", status_code=404, media_type="text/plain")

    return Response(
        json.dumps(item, separators=(",", ":"), ensure_ascii=False),
        media_type="application/json",
    )
