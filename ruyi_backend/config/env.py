from typing import Annotated, TypeAlias

from fastapi import Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBConfig(BaseModel):
    """Configuration for a SQLAlchemy DB connection."""

    dsn: str = ""
    name: str = "ruyisdk"


class ESConfig(BaseModel):
    """Configuration for an Elasticsearch connection."""

    host: str = ""
    basic_auth: str = ""


class EnvConfig(BaseSettings, case_sensitive=False):
    """Environment config for the backend service."""

    model_config = SettingsConfigDict(
        env_prefix="RUYI_BACKEND_",
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
    )
    debug: bool = False
    db_main: DBConfig = DBConfig()
    es_main: ESConfig = ESConfig()


_ENV_CONFIG: EnvConfig | None = None


def get_env_config() -> EnvConfig:
    if _ENV_CONFIG is None:
        init_env_config()
        assert _ENV_CONFIG is not None
    return _ENV_CONFIG


def init_env_config() -> None:
    global _ENV_CONFIG
    if _ENV_CONFIG is None:
        _ENV_CONFIG = EnvConfig()


DIEnvConfig: TypeAlias = Annotated[EnvConfig, Depends(get_env_config)]
