from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from ..config.env import get_env_config, init_env_config
from ..db.conn import init_main_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_env_config()
    cfg = get_env_config()
    init_main_db(cfg)
    app.debug = cfg.debug
    if not cfg.debug:
        app.docs_url = None
        app.redoc_url = None
        app.openapi_url = None

    yield

    # no teardown logic for now
