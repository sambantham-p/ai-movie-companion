"""Redis client factory and shared key names.

Redis serves three roles: the ARQ job queues, short-lived caches (e.g. seat snapshots), and
worker heartbeats. All key names live here so producers and consumers cannot drift apart.
"""

from __future__ import annotations

from redis.asyncio import Redis

from movie_companion.core.config import Settings

KEY_PREFIX = "mc"


def heartbeat_key(service: str) -> str:
    """Redis key a worker refreshes to signal it is alive (e.g. 'mc:heartbeat:browser')."""
    return f"{KEY_PREFIX}:heartbeat:{service}"


def create_redis(settings: Settings) -> Redis:
    """Build an async Redis client that decodes responses to str."""
    client: Redis = Redis.from_url(
        settings.redis_url, decode_responses=True, health_check_interval=30
    )
    return client
