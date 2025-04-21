from typing import Annotated, Any, TypeAlias

from fastapi import Depends
from githubkit import GitHub

from ..config.env import DIEnvConfig

_GITHUB: GitHub[Any] | None = None


def get_github() -> GitHub[Any]:
    if _GITHUB is not None:
        return _GITHUB
    raise RuntimeError("GitHub client not initialized")


def init_github(cfg: DIEnvConfig) -> None:
    global _GITHUB
    _GITHUB = GitHub(
        auth=cfg.github.api_token,
        base_url=cfg.github.base_url,
        user_agent=cfg.github.user_agent,
    )


DIGitHub: TypeAlias = Annotated[GitHub[Any], Depends(get_github)]
"""Dependency on the global GitHub client instance."""
