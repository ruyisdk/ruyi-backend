from typing import Annotated, TypeAlias

from fastapi import Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBConfig(BaseModel):
    dsn: str = ""
    name: str = "ruyisdk"


class EnvConfig(BaseSettings, case_sensitive=False):
    model_config = SettingsConfigDict(
        env_prefix="RUYI_BACKEND_",
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
    )
    debug: bool = False
    db_main: DBConfig = DBConfig()


_ENV_CONFIG: EnvConfig | None = None


def get_env_config() -> EnvConfig:
    if _ENV_CONFIG is not None:
        return _ENV_CONFIG
    raise RuntimeError("EnvConfig not initialized")


def init_env_config() -> None:
    global _ENV_CONFIG
    _ENV_CONFIG = EnvConfig()


DIEnvConfig: TypeAlias = Annotated[EnvConfig, Depends(get_env_config)]
