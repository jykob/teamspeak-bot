from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

type CacheKey = tuple[Any, ...]
type Cache = dict[CacheKey, CacheRecord]


class CacheRecord(NamedTuple):
    timestamp: float
    record: Any


class _Cache:
    def __init__(self, max_ttl: float) -> None:
        self._cache: Cache = dict()
        self._max_ttl = max_ttl

    def get(self, key: CacheKey, max_ttl: float) -> Any | None:
        cache_hit = self._cache.get(key)
        if cache_hit is None:
            return None

        now = time.monotonic()
        if cache_hit.timestamp + max_ttl < now:
            return None

        return cache_hit.record

    def add(self, key: CacheKey, data: Any) -> None:
        self._cache[key] = CacheRecord(time.monotonic(), data)

    def purge(self) -> None:
        now = time.monotonic()

        to_be_deleted = tuple(
            key for key, item in self._cache.items() if item.timestamp + self._max_ttl < now
        )

        for key in to_be_deleted:
            del self._cache[key]


_cache = _Cache(max_ttl=60 * 10)
_cache_lock = asyncio.Lock()


async def with_cache[T, *Ts](
    func: Callable[[*Ts], Coroutine[None, None, T]], *args: *Ts, max_ttl: int
) -> T:
    async with _cache_lock:
        _cache.purge()

        if hit := _cache.get(args, max_ttl):
            return hit

        result = await func(*args)
        _cache.add(args, result)

        return result
