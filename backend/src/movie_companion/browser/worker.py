"""ARQ settings for the browser worker (home machine only).

Run with: `uv run arq movie_companion.browser.worker.WorkerSettings`.
Consumes the `browser` queue one job at a time: the browser is a single, shared resource and
the research guardrails require serialised page loads. Seat reading and booking jobs are
registered here in later milestones.
"""

from __future__ import annotations

from typing import Any, ClassVar

from arq import cron
from arq.connections import RedisSettings

from movie_companion.browser.session import BrowserSession
from movie_companion.cache.redis import create_redis
from movie_companion.core.config import get_settings
from movie_companion.core.logging import get_logger, setup_logging
from movie_companion.core.request_context import set_request_id
from movie_companion.jobs import heartbeat
from movie_companion.jobs.queues import BROWSER_QUEUE

SERVICE = "browser"
logger = get_logger(__name__)


async def browser_ping(ctx: dict[str, Any]) -> dict[str, str]:
    """Round-trip check: proves the worker is consuming and the browser is up."""
    set_request_id(ctx.get("job_id"))
    session: BrowserSession = ctx["browser"]
    return {"service": SERVICE, "status": "ok", "browser": session.browser_version()}


async def send_heartbeat(ctx: dict[str, Any]) -> None:
    """Cron job: refresh this worker's heartbeat key."""
    await heartbeat.beat(ctx["app_redis"], SERVICE)


async def on_startup(ctx: dict[str, Any]) -> None:
    """Configure logging, start the browser session and announce the worker."""
    setup_logging(SERVICE)
    settings = get_settings()
    ctx["app_redis"] = create_redis(settings)
    session = BrowserSession(settings)
    await session.start()
    ctx["browser"] = session
    await heartbeat.beat(ctx["app_redis"], SERVICE)
    logger.info(
        "Browser worker started on queue %s (mode=%s)", BROWSER_QUEUE, settings.browser_mode
    )


async def on_shutdown(ctx: dict[str, Any]) -> None:
    """Stop the browser session and close Redis."""
    if "browser" in ctx:
        await ctx["browser"].stop()
    await ctx["app_redis"].aclose()
    logger.info("Browser worker stopped")


class WorkerSettings:
    """ARQ entry point for the browser worker."""

    functions: ClassVar[list[Any]] = [browser_ping]
    cron_jobs: ClassVar[list[Any]] = [cron(send_heartbeat, second=0, run_at_startup=False)]
    on_startup = on_startup
    on_shutdown = on_shutdown
    queue_name = BROWSER_QUEUE
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 1  # one browser, one job at a time
    job_timeout = 600
