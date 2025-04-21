from typing import Annotated, TypeAlias

from fastapi import Depends
from redis.asyncio.client import Redis

from ..config.env import DIEnvConfig
from .store import CacheStore

_MAIN_REDIS_CONN: Redis | None = None
_STORE: CacheStore | None = None


def get_main_redis() -> Redis:
    if _MAIN_REDIS_CONN is not None:
        return _MAIN_REDIS_CONN
    raise RuntimeError("Main Redis connection not initialized")


def get_cache_store() -> CacheStore:
    if _STORE is not None:
        return _STORE
    raise RuntimeError("Cache store not initialized")


def init_main_redis(cfg: DIEnvConfig) -> None:
    global _MAIN_REDIS_CONN
    global _STORE

    conn = Redis.from_url(cfg.cache_main.host)

    # we do our own (de)serialization, so force the option here, in case it is
    # specified on the connection URL
    conn.get_connection_kwargs()["decode_responses"] = False

    store = CacheStore(conn)

    _MAIN_REDIS_CONN = conn
    _STORE = store


DIMainRedis: TypeAlias = Annotated[Redis, Depends(get_main_redis)]
"""Dependency on the main Redis connection."""

DICacheStore: TypeAlias = Annotated[CacheStore, Depends(get_cache_store)]
"""Dependency on the application cache store."""

# Keys.
KEY_TELEMETRY_DATA_LAST_PROCESSED = "telemetry:last-processed"
"""Last processed time of raw telemetry data."""

KEY_GITHUB_RELEASE_STATS = "github:release-stats"
"""GitHub release stats data."""

KEY_FRONTEND_DASHBOARD = "frontend:dashboard"
"""Frontend dashboard data."""
