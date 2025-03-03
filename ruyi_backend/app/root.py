from typing import Any, Final

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config.env import get_env_config
from .lifespan import lifespan


def _init_fastapi() -> FastAPI:
    cfg = get_env_config()

    kwargs: dict[str, Any] = {}
    if not cfg.debug:
        kwargs["docs_url"] = None
        kwargs["openapi_url"] = None
        kwargs["redoc_url"] = None
    app = FastAPI(lifespan=lifespan, **kwargs)

    cors_origins = cfg.http.cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app: Final[FastAPI] = _init_fastapi()
