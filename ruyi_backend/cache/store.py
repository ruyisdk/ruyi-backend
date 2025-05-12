from inspect import isawaitable
from typing import Any

import msgpack
from redis.asyncio.client import Redis


class CacheStore:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis
        self._prefix = "ruyi-backend:"

    def _get_prefixed_key(self, key: str) -> str:
        return self._prefix + key

    async def ping(self) -> None:
        await self._redis.ping()

    async def get(self, key: str) -> Any | None:
        key = self._get_prefixed_key(key)
        val = await self._redis.get(key)
        if val is None:
            return None
        if not isinstance(val, bytes):
            raise TypeError("Redis response not in raw bytes")
        return msgpack.loads(val, timestamp=3)

    async def set(
        self,
        key: str,
        val: Any,
        nx: bool = False,
        xx: bool = False,
    ) -> Any:
        key = self._get_prefixed_key(key)
        payload = msgpack.dumps(val, datetime=True)
        # TODO: handle the response according to the protocol
        return await self._redis.set(
            key,
            payload,
            nx=nx,
            xx=xx,
        )

    async def hget(self, name: str, key: str) -> Any:
        name = self._get_prefixed_key(name)
        v = self._redis.hget(name, key)
        val = await v if isawaitable(v) else v
        if val is None:
            return None
        return msgpack.loads(val.encode("latin-1"), timestamp=3)

    async def hgetall(self, name: str) -> dict[str, Any]:
        name = self._get_prefixed_key(name)
        v = self._redis.hgetall(name)
        val = await v if isawaitable(v) else v
        return {
            k.decode("utf-8"): msgpack.loads(v, timestamp=3) for k, v in val.items()
        }

    async def hset(
        self,
        name: str,
        key: str,
        val: Any,
    ) -> Any:
        name = self._get_prefixed_key(name)
        payload = msgpack.dumps(val, datetime=True)
        # TODO: handle the response according to the protocol
        v = self._redis.hset(
            name,
            key,
            payload,  # type: ignore[arg-type]  # bytes is actually accepted
        )
        return await v if isawaitable(v) else v
