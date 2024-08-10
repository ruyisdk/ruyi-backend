from typing import Any, Awaitable, Callable, Coroutine

from fastapi.responses import JSONResponse

async def default_handler(**kwargs: object) -> dict[str, Any]: ...
def health(
    conditions: list[Callable[..., dict[str, Any] | bool]],
    *,
    success_handler: Callable[..., Awaitable[Any]] = ...,
    failure_handler: Callable[..., Awaitable[Any]] = ...,
    success_status: int = 200,
    failure_status: int = 503,
) -> Callable[..., Coroutine[Any, Any, JSONResponse]]: ...
