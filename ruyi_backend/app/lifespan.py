from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from ..config import get_env_config, init
from ..db.conn import dispose_main_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init()
    cfg = get_env_config()

    app.debug = cfg.debug
    if not cfg.debug:
        app.docs_url = None
        app.redoc_url = None
        app.openapi_url = None

    try:
        yield
    finally:
        await dispose_main_db()
