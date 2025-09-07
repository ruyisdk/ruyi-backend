from typing import Final

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse

from ..config.env import get_env_config
from ..components.auth import DIBasicDev
from .lifespan import lifespan


def _init_fastapi() -> FastAPI:
    cfg = get_env_config()

    # Always disable default doc endpoints so we can conditionally mount our own
    # protected endpoints below
    app = FastAPI(
        lifespan=lifespan,
        docs_url=None,
        openapi_url=None,
        redoc_url=None,
    )

    cors_origins = cfg.http.cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if not cfg.debug:
        return app

    OPENAPI_PATH = "/openapi.json"

    @app.get(OPENAPI_PATH, include_in_schema=False)
    def openapi_json(_: DIBasicDev) -> JSONResponse:
        return JSONResponse(app.openapi())

    @app.get("/docs", include_in_schema=False)
    def docs(_: DIBasicDev) -> HTMLResponse:
        return get_swagger_ui_html(openapi_url=OPENAPI_PATH, title="Swagger UI")

    @app.get("/redoc", include_in_schema=False)
    def redoc(_: DIBasicDev) -> HTMLResponse:
        return get_redoc_html(openapi_url=OPENAPI_PATH, title="ReDoc")

    return app


app: Final[FastAPI] = _init_fastapi()
