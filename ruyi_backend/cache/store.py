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

    async def get(self, key: str) -> Any:
        key = self._get_prefixed_key(key)
        val = await self._redis.get(key)
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
