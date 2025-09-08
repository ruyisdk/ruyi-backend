import asyncio
import datetime
from typing import Any, TypedDict

from githubkit import GitHub
from pydantic import BaseModel

ASSET_DOWNLOAD_STATS_GRAPHQL = """
query AssetDownloadsStats($owner: String!, $name: String!, $cursor: String, $pageSize: Int = 50) {
  repository(owner: $owner, name: $name) {
    releases(first: $pageSize, after: $cursor) {
      nodes {
        tagName
        publishedAt
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

GITHUB_ORG_STATS_GRAPHQL = """
query OrgStats($org: String!, $cursor: String, $pageSize: Int) {
  organization(login: $org) {
    repositories(first: $pageSize, after: $cursor) {
      nodes {
        name
        forkCount
        issues {
          totalCount
        }
        pullRequests {
          totalCount
        }
        stargazerCount
        watchers {
          totalCount
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
    date: datetime.datetime
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
            date = datetime.datetime.fromisoformat(rel["publishedAt"])
            assets = [
                AssetDownloadStats(name=a["name"], download_count=a["downloadCount"])
                for a in rel["releaseAssets"]["nodes"]
            ]
            result.append(ReleaseDownloadStats(tag=tag, date=date, assets=assets))
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


class GitHubRepoStats(BaseModel):
    name: str
    watchers_count: int
    forks_count: int
    stars_count: int
    prs_count: int
    issues_count: int
    contributors: list[str]


class GitHubOrgStats(BaseModel):
    name: str
    watchers_count: int
    forks_count: int
    stars_count: int
    prs_count: int
    issues_count: int
    contributors_count: int
    detail_by_repo: list[GitHubRepoStats]


async def _list_repo_contributors(
    g: GitHub[Any],
    owner: str,
    repo: str,
    page_size: int = 100,
) -> list[str]:
    result = []
    page = 0
    while True:
        resp = await g.rest.repos.async_list_contributors(
            owner,
            repo,
            anon="true",
            per_page=page_size,
            page=page,
        )
        contributors = resp.parsed_data
        if not contributors:
            break

        for c in contributors:
            # Either login or email should be present; email will be absent for
            # users with matched GitHub login, unfortunately.
            # This is going to cause some duplicates in case some contributors
            # are ranked higher in some repos but very low (>500th) in others,
            # but this is not a problem for now; we're still far from 500
            # contributors for any of our repos.
            if c.login:
                result.append(f"github:{c.login}")
                continue
            result.append(f"email:{c.email}")

        page += 1

    return result


async def query_org_stats(
    g: GitHub[Any],
    org: str,
    page_size: int = 20,
) -> GitHubOrgStats:
    repo_stats = []
    cursor: str | None = None
    while True:
        resp = await g.async_graphql(
            GITHUB_ORG_STATS_GRAPHQL,
            variables={"org": org, "cursor": cursor, "pageSize": page_size},
        )

        data = resp["organization"]["repositories"]["nodes"]
        contributors = await asyncio.gather(
            *[_list_repo_contributors(g, org, r["name"]) for r in data]
        )
        for r, c in zip(data, contributors):
            repo_stats.append(
                GitHubRepoStats(
                    name=r["name"],
                    forks_count=r["forkCount"],
                    issues_count=r["issues"]["totalCount"],
                    prs_count=r["pullRequests"]["totalCount"],
                    stars_count=r["stargazerCount"],
                    watchers_count=r["watchers"]["totalCount"],
                    contributors=c,
                )
            )

        page_info = data["pageInfo"]
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    all_contributors = set()
    for r in repo_stats:
        all_contributors.update(r.contributors)

    return GitHubOrgStats(
        name=org,
        watchers_count=sum(r.watchers_count for r in repo_stats),
        forks_count=sum(r.forks_count for r in repo_stats),
        stars_count=sum(r.stars_count for r in repo_stats),
        prs_count=sum(r.prs_count for r in repo_stats),
        issues_count=sum(r.issues_count for r in repo_stats),
        contributors_count=len(all_contributors),
        detail_by_repo=repo_stats,
    )
