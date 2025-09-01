import pathlib
from typing import Any

__version__: str
BASE_URL: str
CACHE_DIR: pathlib.Path
USER_AGENT: str

def pypi_stats_api(
    endpoint: str,
    params: str | None = None,
    format: str | None = "pretty",
    start_date: str | None = None,
    end_date: str | None = None,
    sort: bool = True,
    total: str = "all",
    color: str = "yes",
    verbose: bool = False,
): ...
def recent(package: str, period: str | None = None, **kwargs: Any): ...
def overall(package: str, mirrors: bool | str | None = None, **kwargs: Any): ...
def python_major(package: str, version: str | None = None, **kwargs: Any): ...
def python_minor(package: str, version: str | None = None, **kwargs: Any) -> str: ...
def system(package: str, os: str | None = None, **kwargs: Any): ...
