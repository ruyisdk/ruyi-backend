from fastapi import APIRouter, Response

from ..cache import DICacheStore
from ..components.news_items import NEWS_ITEM_NOT_FOUND, get_news_item_markdown

router = APIRouter(prefix="/news")


@router.get("/get/{item_id}.json")
async def get_news_item_markdown_v1(
    item_id: str,
    cache: DICacheStore,
    response: Response,
) -> dict[str, str]:
    """Returns the news item in Markdown format."""

    item = await get_news_item_markdown(item_id, cache)
    if not item:
        response.status_code = 404
        return NEWS_ITEM_NOT_FOUND

    return item
