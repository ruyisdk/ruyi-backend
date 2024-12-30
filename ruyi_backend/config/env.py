from functools import lru_cache
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


@lru_cache
def get_env_settings() -> EnvConfig:
    return EnvConfig()


DIEnvConfig: TypeAlias = Annotated[EnvConfig, Depends(get_env_settings)]
