"""Enqueueing helper used by the API to hand work to either worker."""

from __future__ import annotations

from typing import Any

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings
from arq.jobs import Job

from movie_companion.core.config import Settings


class JobQueue:
    """Lazily connected ARQ producer; one instance per API process."""

    def __init__(self, settings: Settings) -> None:
        self._redis_settings = RedisSettings.from_dsn(settings.redis_url)
        self._pool: ArqRedis | None = None

    async def _get_pool(self) -> ArqRedis:
        if self._pool is None:
            self._pool = await create_pool(self._redis_settings)
        return self._pool

    async def enqueue(self, function: str, queue: str, *args: Any, **kwargs: Any) -> Job | None:
        """Enqueue `function` on `queue`; returns None if an identical job ID already exists."""
        pool = await self._get_pool()
        return await pool.enqueue_job(function, *args, _queue_name=queue, **kwargs)

    async def close(self) -> None:
        """Close the Redis pool if it was opened."""
        if self._pool is not None:
            await self._pool.aclose()
            self._pool = None
