"""Readiness checks for the API's dependencies and worker heartbeats."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine

from movie_companion.core.logging import get_logger
from movie_companion.db.session import ping_database
from movie_companion.jobs import heartbeat
from movie_companion.schemas.health import DependencyCheck, ReadinessResponse, WorkerStatus

logger = get_logger(__name__)
CHECK_TIMEOUT_SECONDS = 3.0
WORKER_SERVICES = ("jobs", "browser")


async def _timed(name: str, probe: Callable[[], Awaitable[object]]) -> DependencyCheck:
    """Run one probe with a timeout and report its status and latency."""
    started = time.perf_counter()
    try:
        await asyncio.wait_for(probe(), timeout=CHECK_TIMEOUT_SECONDS)
    except Exception as exc:
        logger.warning("Readiness check failed for %s: %s", name, exc)
        return DependencyCheck(status="error", error=type(exc).__name__)
    return DependencyCheck(status="ok", latency_ms=round((time.perf_counter() - started) * 1000, 2))


async def check_readiness(engine: AsyncEngine, redis: Redis) -> ReadinessResponse:
    """Check Postgres and Redis, and collect worker heartbeats."""
    database, cache = await asyncio.gather(
        _timed("database", lambda: ping_database(engine)),
        _timed("redis", redis.ping),
    )
    workers: dict[str, WorkerStatus] = {}
    if cache.status == "ok":
        for service in WORKER_SERVICES:
            seen = await heartbeat.last_seen(redis, service)
            workers[service] = WorkerStatus(online=seen is not None, last_seen=seen)
    ready = database.status == "ok" and cache.status == "ok"
    return ReadinessResponse(
        status="ready" if ready else "not_ready", database=database, redis=cache, workers=workers
    )
