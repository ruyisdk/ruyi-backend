import datetime
from typing import TypedDict, TypeGuard

import aiohttp
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql.expression import func, select

from ..db.schema import ModelDownloadStatsDailyPyPI, download_stats_daily_pypi

PYPISTATS_API_BASE_URL = "https://pypistats.org/api/"


class PyPIStatsDataPoint(TypedDict):
    category: str  # "without_mirrors", "with_mirrors"
    date: str  # YYYY-MM-DD
    downloads: int


def _is_pypistats_data_point(obj: object) -> TypeGuard[PyPIStatsDataPoint]:
    if not isinstance(obj, dict):
        return False

    if "category" not in obj or not isinstance(obj["category"], str):
        return False
    if "date" not in obj or not isinstance(obj["date"], str):
        return False
    if "downloads" not in obj or not isinstance(obj["downloads"], int):
        return False

    return True


class PyPIStatsResponse(TypedDict):
    data: list[PyPIStatsDataPoint]
    package: str
    type: str  # "overall_downloads" etc.


def _is_pypi_stats_response(obj: object) -> TypeGuard[PyPIStatsResponse]:
    if not isinstance(obj, dict):
        return False

    if "package" not in obj or not isinstance(obj["package"], str):
        return False
    if "type" not in obj or not isinstance(obj["type"], str):
        return False
    if "data" not in obj or not isinstance(obj["data"], list):
        return False

    for item in obj["data"]:
        if not _is_pypistats_data_point(item):
            return False

    return True


async def _query_overall(package_name: str) -> list[PyPIStatsDataPoint]:
    url = f'{PYPISTATS_API_BASE_URL}packages/{package_name}/overall'
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, params={"mirrors": "false"}) as resp:
            obj = await resp.json()

    if not _is_pypi_stats_response(obj):
        raise ValueError("Unexpected response format of pypistats")

    return obj["data"]


async def fetch_pypi_download_stats(
    package_name: str,
) -> dict[datetime.date, int]:
    """Fetches the download stats for a given PyPI package.

    Returns a dictionary containing daily download stats keyed by date.
    """

    stats = await _query_overall(package_name)
    result = {}
    for p in stats:
        dt = datetime.datetime.strptime(p["date"], "%Y-%m-%d").date()
        result[dt] = p["downloads"]

    return result


async def persist_pypi_download_stats(
    conn: AsyncConnection,
    package_name: str,
    stats: dict[datetime.date, int],
) -> None:
    """Persists the given PyPI download stats into the database.

    Existing entries for the same (package_name, version, date) will be untouched.
    """

    buf: list[ModelDownloadStatsDailyPyPI] = []
    for date, count in stats.items():
        buf.append(
            ModelDownloadStatsDailyPyPI(
                name=package_name,
                version="*",
                date=datetime.datetime(date.year, date.month, date.day),
                count=count,
            ),
        )

    if not buf:
        return

    await conn.execute(
        download_stats_daily_pypi.insert().prefix_with("IGNORE"),
        buf,
    )


async def sum_pypi_download_stats(
    conn: AsyncConnection,
    date_start: datetime.date,
    date_end: datetime.date,
    package_name: str,
    version: str = "*",
) -> int:
    """Queries the total download counts for a given package in the given date range,
    using data persisted in the database."""

    total = await conn.scalar(
        select(func.sum(download_stats_daily_pypi.c.count)).where(
            download_stats_daily_pypi.c.name == package_name,
            download_stats_daily_pypi.c.version == version,
            download_stats_daily_pypi.c.date
            >= datetime.datetime(date_start.year, date_start.month, date_start.day),
            download_stats_daily_pypi.c.date
            < datetime.datetime(date_end.year, date_end.month, date_end.day),
        )
    )
    return total or 0
