from typing import Any, Final

from fastapi import FastAPI

from ..config.env import get_env_config
from .lifespan import lifespan


def _init_fastapi() -> FastAPI:
    kwargs: dict[str, Any] = {}
    if not get_env_config().debug:
        kwargs["docs_url"] = None
        kwargs["openapi_url"] = None
        kwargs["redoc_url"] = None
    return FastAPI(lifespan=lifespan, **kwargs)


app: Final[FastAPI] = _init_fastapi()
