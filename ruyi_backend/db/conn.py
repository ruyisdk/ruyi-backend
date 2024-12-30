from functools import lru_cache
from typing import Annotated, TypeAlias

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from ..config.env import DIEnvConfig


@lru_cache
def get_main_db(cfg: DIEnvConfig) -> AsyncEngine:
    return create_async_engine(cfg.db_main.dsn, echo=cfg.debug)


DIMainDB: TypeAlias = Annotated[AsyncEngine, Depends(get_main_db)]
