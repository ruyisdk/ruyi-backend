from typing import Any, TypedDict

from githubkit import GitHub

ASSET_DOWNLOAD_STATS_GRAPHQL = """
query AssetDownloadsStats($owner: String!, $name: String!, $cursor: String, $pageSize: Int = 50) {
  repository(owner: $owner, name: $name) {
    releases(first: $pageSize, after: $cursor) {
      nodes {
        tagName
        releaseAssets(first: 16) {
          nodes {
            name
            downloadCount
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""


class AssetDownloadStats(TypedDict):
    name: str
    download_count: int


class ReleaseDownloadStats(TypedDict):
    tag: str
    assets: list[AssetDownloadStats]


async def query_release_downloads(
    g: GitHub[Any],
    repo: str,
) -> list[ReleaseDownloadStats]:
    """Fetches release download counts for all releases of the given repo."""
    owner, name = repo.split("/")
    result: list[ReleaseDownloadStats] = []

    release_cursor: str | None = None
    while True:
        resp = await g.async_graphql(
            ASSET_DOWNLOAD_STATS_GRAPHQL,
            variables={"owner": owner, "name": name, "cursor": release_cursor},
        )
        data = resp["repository"]["releases"]
        for rel in data["nodes"]:
            tag = rel["tagName"]
            assets = [
                AssetDownloadStats(name=a["name"], download_count=a["downloadCount"])
                for a in rel["releaseAssets"]["nodes"]
            ]
            result.append(ReleaseDownloadStats(tag=tag, assets=assets))
        page_info = data["pageInfo"]
        if not page_info.get("hasNextPage"):
            break
        release_cursor = page_info.get("endCursor")

    return result


def merge_download_counts(
    stats: list[ReleaseDownloadStats],
) -> int:
    """Counts total downloads across all releases."""
    total = 0
    for rel in stats:
        for asset in rel["assets"]:
            total += asset["download_count"]
    return total
