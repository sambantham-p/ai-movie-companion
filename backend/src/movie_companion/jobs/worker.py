"""ARQ settings for the cloud-safe jobs worker.

Run with: `uv run arq movie_companion.jobs.worker.WorkerSettings`.
Feature jobs (TMDB sync, score recompute, alert dispatch) are registered in `functions`
and `cron_jobs` as their milestones land.
"""

from __future__ import annotations

from typing import Any, ClassVar

from arq import cron
from arq.connections import RedisSettings

from movie_companion.cache.redis import create_redis
from movie_companion.core.config import get_settings
from movie_companion.core.logging import get_logger, setup_logging
from movie_companion.core.request_context import set_request_id
from movie_companion.jobs import heartbeat
from movie_companion.jobs.queues import JOBS_QUEUE

SERVICE = "jobs"
logger = get_logger(__name__)


async def ping(ctx: dict[str, Any]) -> dict[str, str]:
    """Round-trip check used by health tests: proves the worker consumes this queue."""
    set_request_id(ctx.get("job_id"))
    logger.info("ping received")
    return {"service": SERVICE, "status": "ok"}


async def send_heartbeat(ctx: dict[str, Any]) -> None:
    """Cron job: refresh this worker's heartbeat key."""
    await heartbeat.beat(ctx["app_redis"], SERVICE)


async def on_startup(ctx: dict[str, Any]) -> None:
    """Configure logging and shared clients when the worker boots."""
    setup_logging(SERVICE)
    ctx["app_redis"] = create_redis(get_settings())
    await heartbeat.beat(ctx["app_redis"], SERVICE)
    logger.info("Jobs worker started on queue %s", JOBS_QUEUE)


async def on_shutdown(ctx: dict[str, Any]) -> None:
    """Close shared clients."""
    await ctx["app_redis"].aclose()
    logger.info("Jobs worker stopped")


class WorkerSettings:
    """ARQ entry point for the jobs worker."""

    functions: ClassVar[list[Any]] = [ping]
    cron_jobs: ClassVar[list[Any]] = [cron(send_heartbeat, second=0, run_at_startup=False)]
    on_startup = on_startup
    on_shutdown = on_shutdown
    queue_name = JOBS_QUEUE
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 10
    job_timeout = 300
