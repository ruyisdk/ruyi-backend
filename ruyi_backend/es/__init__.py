from typing import Annotated, TypeAlias

from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from ..config.env import DIEnvConfig

_MAIN_ES_CONN: AsyncElasticsearch | None = None


def get_main_es() -> AsyncElasticsearch:
    if _MAIN_ES_CONN is not None:
        return _MAIN_ES_CONN
    raise RuntimeError("Main Elasticsearch connection not initialized")


def init_main_es(cfg: DIEnvConfig) -> None:
    global _MAIN_ES_CONN
    username, password = cfg.es_main.basic_auth.split(":", 1)
    _MAIN_ES_CONN = AsyncElasticsearch(
        cfg.es_main.host,
        basic_auth=(username, password),
    )


DIMainES: TypeAlias = Annotated[AsyncElasticsearch, Depends(get_main_es)]
"""Dependency on the main Elasticsearch connection."""
