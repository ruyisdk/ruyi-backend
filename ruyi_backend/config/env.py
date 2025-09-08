import functools
from typing import Annotated, Any, TypeAlias

from fastapi import Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthCredConfig(BaseModel):
    """Credential for a user."""

    name: str = ""
    psw_hash: str = ""


class AuthConfig(BaseModel):
    """Configuration for authentication."""

    admins: list[AuthCredConfig] = []
    """Site administrators able to perform privileged actions."""

    devs: list[AuthCredConfig] = []
    """Developers allowed to access the FastAPI documentation endpoints."""

    site_secret: str = ""

    @functools.cached_property
    def admins_by_name(self) -> dict[str, AuthCredConfig]:
        return {ac.name: ac for ac in self.admins}

    @functools.cached_property
    def devs_by_name(self) -> dict[str, AuthCredConfig]:
        return {ac.name: ac for ac in self.devs}


class DBConfig(BaseModel):
    """Configuration for a SQLAlchemy DB connection."""

    dsn: str = ""
    name: str = "ruyisdk"


class ESConfig(BaseModel):
    """Configuration for an Elasticsearch connection."""

    host: str = ""
    basic_auth: str = ""


class GitHubConfig(BaseModel):
    """Configuration for GitHub API access."""

    api_token: str = ""
    base_url: str = "https://api.github.com"
    user_agent: str = ""

    ruyi_org: str = "ruyisdk"
    ruyi_backend_repo: str = "ruyisdk/ruyi-backend"
    ruyi_ide_eclipse_repo: str = "ruyisdk/ruyisdk-eclipse-plugins"
    ruyi_packages_index_repo: str = "ruyisdk/packages-index"
    ruyi_pm_repo: str = "ruyisdk/ruyi"

    def model_post_init(self, context: Any) -> None:
        super().model_post_init(context)
        self.user_agent = self.user_agent or self.ruyi_backend_repo


class PyPIConfig(BaseModel):
    """Configuration for PyPI access."""

    ruyi_pm_package: str = "ruyi"


class HTTPConfig(BaseModel):
    """Configuration for an HTTP client."""

    cors_origins: list[str] = ["*"]


class RedisConfig(BaseModel):
    """Configuration for a Redis connection."""

    host: str = ""


class ReleaseWorkerConfig(BaseModel):
    """Configuration for the release worker."""

    rsync_staging_dir: str = ""
    rsync_remote_url: str = ""
    rsync_remote_pass: str = ""


class CLIConfig(BaseModel):
    """Configuration for the CLI management client."""

    release_worker: ReleaseWorkerConfig = ReleaseWorkerConfig()


class EnvConfig(BaseSettings, case_sensitive=False):
    """Environment config for the backend service."""

    model_config = SettingsConfigDict(
        env_prefix="RUYI_BACKEND_",
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
    )
    debug: bool = False
    auth: AuthConfig = AuthConfig()
    cache_main: RedisConfig = RedisConfig()
    cli: CLIConfig = CLIConfig()
    db_main: DBConfig = DBConfig()
    es_main: ESConfig = ESConfig()
    github: GitHubConfig = GitHubConfig()
    http: HTTPConfig = HTTPConfig()
    pypi: PyPIConfig = PyPIConfig()


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
