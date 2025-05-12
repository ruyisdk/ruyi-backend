from asyncio import gather
import re
from typing import Any, NamedTuple, TypedDict, cast

from githubkit import GitHub

from ..cache import KEY_PREFIX_NEWS_ITEM_CONTENT, KEY_PREFIX_NEWS_ITEM_HASH
from ..cache.store import CacheStore


class GitHubLinks(TypedDict):
    git: str | None
    html: str | None
    self: str


class GitHubContentTreeEntry(TypedDict):
    type: str
    size: int
    name: str
    path: str
    sha: str
    url: str
    git_url: str | None
    html_url: str | None
    download_url: str | None
    _links: GitHubLinks


class GitHubContentTree(TypedDict):
    type: str
    size: int
    name: str
    path: str
    sha: str
    url: str
    git_url: str | None
    html_url: str | None
    download_url: str | None
    _links: GitHubLinks

    # Optional fields based on content type

    # Present for files
    content: str | None
    # Present when content is included
    encoding: str | None
    # Present for directories
    entries: list[GitHubContentTreeEntry] | None


class NewsItemFileInfo(NamedTuple):
    id: str
    lang_code: str
    content_hash: str
    download_url: str

    @property
    def hash_cache_key(self) -> str:
        return f"{KEY_PREFIX_NEWS_ITEM_HASH}{self.id}:{self.lang_code}"

    @property
    def content_cache_key(self) -> str:
        return f"{KEY_PREFIX_NEWS_ITEM_CONTENT}{self.id}"


RE_NEWS_ITEM_FILE_NAME = re.compile(
    r"^([0-9]{4}-[0-9]{2}-[0-9]{2})-(.*)\.([A-Za-z_]+)\.md$"
)


async def refresh_news_items(
    g: GitHub[Any],
    cache: CacheStore,
    repo: str,
) -> None:
    """Refreshes news items from the given RuyiSDK software repo."""

    news_item_infos = await query_news_item_info(g, repo)
    if not news_item_infos:
        # no news items
        return

    # determine which of the news items have changed, and update the outdated
    # ones
    await gather(*[maybe_update_news_item(g, cache, item) for item in news_item_infos])


async def query_news_item_info(
    g: GitHub[Any],
    repo: str,
) -> list[NewsItemFileInfo]:
    """Queries the news items from the given RuyiSDK software repo."""

    owner, name = repo.split("/")

    # NOTE: according to the GitHub API documentation, the endpoint has a
    # limitation of 1000 directory entries, but we don't expect to have so many
    # news items for the forseeable future.
    resp = await g.arequest(
        "GET",
        f"/repos/{owner}/{name}/contents/news",
        headers={
            "Accept": "application/vnd.github.object+json",
        },
    )
    data = cast(GitHubContentTree, resp.json())
    if data["entries"] is None:
        # should not happen
        return []

    # Figure out the IDs, language codes and respective content hashes
    # for each news item
    result: list[NewsItemFileInfo] = []
    for x in data["entries"]:
        if x["type"] != "file" or not x["path"].endswith(".md"):
            # we only care about Markdown files
            continue

        # like "2025-04-22-ruyi-0.32.zh_CN.md"
        m = RE_NEWS_ITEM_FILE_NAME.match(x["name"])
        if not m:
            # we only care about files that match the naming convention
            continue
        id, lang_code = m.group(2), m.group(3)

        result.append(
            NewsItemFileInfo(
                id=id,
                lang_code=lang_code,
                content_hash=x["sha"],
                download_url=x["download_url"] or x["url"],
            )
        )

    return result


async def is_news_item_up_to_date(
    cache: CacheStore,
    item: NewsItemFileInfo,
) -> bool:
    """Checks if the news item is up to date in the cache."""

    cached_hash = await cache.get(item.hash_cache_key)
    if cached_hash is None:
        return False
    if not isinstance(cached_hash, str):
        # unexpected type, assume the item is not up to date
        return False

    return cached_hash == item.content_hash


async def maybe_update_news_item(
    g: GitHub[Any],
    cache: CacheStore,
    item: NewsItemFileInfo,
) -> None:
    """Updates the news item in the cache if it is not up to date."""

    # check if the item is up to date
    if await is_news_item_up_to_date(cache, item):
        return

    # download the content
    resp = await g.arequest(
        "GET",
        item.download_url,
        headers={
            "Accept": "application/vnd.github.raw",
        },
    )

    # update the cache
    await cache.set(item.hash_cache_key, item.content_hash)
    await cache.hset(item.content_cache_key, item.lang_code, resp.text)


async def get_news_item_markdown(
    item_id: str,
    cache: CacheStore,
) -> dict[str, str] | None:
    item = await cache.hgetall(KEY_PREFIX_NEWS_ITEM_CONTENT + item_id)
    return item if item else None
