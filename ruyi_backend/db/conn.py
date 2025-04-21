from typing import Annotated, TypeAlias

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from ..config.env import DIEnvConfig

_DB_ENGINE: AsyncEngine | None = None


def get_main_db() -> AsyncEngine:
    if _DB_ENGINE is not None:
        return _DB_ENGINE
    raise RuntimeError("Main DB not initialized")


def init_main_db(cfg: DIEnvConfig) -> None:
    global _DB_ENGINE

    if cfg.db_main.dsn == "":
        # no DB (maybe we're running from the CLI)
        return

    _DB_ENGINE = create_async_engine(cfg.db_main.dsn, echo=cfg.debug)


DIMainDB: TypeAlias = Annotated[AsyncEngine, Depends(get_main_db)]
