from typing import Annotated, TypeAlias

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from ..config.env import DIEnvConfig

class _MainDBState:
    engine: AsyncEngine | None = None


_MAIN_DB = _MainDBState()
DB_POOL_RECYCLE_SECONDS = 30 * 60


def get_main_db() -> AsyncEngine:
    if _MAIN_DB.engine is not None:
        return _MAIN_DB.engine
    raise RuntimeError("Main DB not initialized")


def init_main_db(cfg: DIEnvConfig) -> None:
    if cfg.db_main.dsn == "":
        # no DB (maybe we're running from the CLI)
        return

    _MAIN_DB.engine = create_async_engine(
        cfg.db_main.dsn,
        echo=cfg.debug,
        pool_pre_ping=True,
        pool_recycle=DB_POOL_RECYCLE_SECONDS,
    )


async def dispose_main_db() -> None:
    if _MAIN_DB.engine is None:
        return

    await _MAIN_DB.engine.dispose()
    _MAIN_DB.engine = None


DIMainDB: TypeAlias = Annotated[AsyncEngine, Depends(get_main_db)]
