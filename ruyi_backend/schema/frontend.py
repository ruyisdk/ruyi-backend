import datetime

from pydantic import BaseModel


class DashboardGitHubRepoStatsV1(BaseModel):
    name: str
    watchers_count: int
    forks_count: int
    stars_count: int
    prs_count: int
    issues_count: int
    # instead of a list of contributor identities, just expose the count for
    # the dashboard for now
    contributors_count: int


class DashboardGitHubOrgStatsV1(BaseModel):
    name: str
    watchers_count: int
    forks_count: int
    stars_count: int
    prs_count: int
    issues_count: int
    contributors_count: int
    detail_by_repo: list[DashboardGitHubRepoStatsV1]


class DashboardEventDetailV1(BaseModel):
    total: int


class DashboardDataV1(BaseModel):
    last_updated: datetime.datetime
    downloads: DashboardEventDetailV1 | None
    """Deprecated: Download numbers of components.

    Use ``downloads_by_categories["components"]`` instead."""
    pm_downloads: DashboardEventDetailV1 | None
    """Deprecated: Download numbers of the package manager.

    Use ``downloads_by_categories["pm"]`` instead."""
    other_categories_downloads: dict[str, DashboardEventDetailV1 | None]
    """Deprecated: Download numbers of other categories provided by the mirror.

    Use ``downloads_by_categories[key]`` instead."""
    downloads_by_categories_v1: dict[str, DashboardEventDetailV1 | None]
    """Download numbers by categories.

    Supersedes `downloads`, `pm_downloads` and `other_categories_downloads`."""
    installs: DashboardEventDetailV1 | None
    top_packages: dict[str, DashboardEventDetailV1 | None]
    top_commands: dict[str, DashboardEventDetailV1 | None]

    github_org_stats: list[DashboardGitHubOrgStatsV1]
    """GitHub organization statistics."""
