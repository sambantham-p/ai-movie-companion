"""Worker heartbeats stored in Redis, read by the API's readiness check."""

from __future__ import annotations

from datetime import UTC, datetime

from redis.asyncio import Redis

from movie_companion.cache.redis import heartbeat_key
from movie_companion.jobs.queues import HEARTBEAT_TTL_SECONDS


async def beat(redis: Redis, service: str) -> None:
    """Record that `service` is alive now; the key expires if beats stop."""
    await redis.set(heartbeat_key(service), datetime.now(UTC).isoformat(), ex=HEARTBEAT_TTL_SECONDS)


async def last_seen(redis: Redis, service: str) -> datetime | None:
    """Return when `service` last reported, or None if it is offline."""
    raw = await redis.get(heartbeat_key(service))
    return datetime.fromisoformat(raw) if raw else None
