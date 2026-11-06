"""FastAPI application factory and API process entry point.

`create_app()` wires settings, logging, middleware, error handlers and routers, and owns the
lifecycle of the database engine, Redis client and job queue. Run with `uv run mc-api`.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from movie_companion import __version__
from movie_companion.api.router import api_router
from movie_companion.cache.redis import create_redis
from movie_companion.core.config import Settings, get_settings
from movie_companion.core.errors import register_exception_handlers
from movie_companion.core.logging import get_logger, setup_logging
from movie_companion.core.request_context import set_request_id
from movie_companion.db.session import create_engine, create_session_factory
from movie_companion.jobs.client import JobQueue

SERVICE = "api"
logger = get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create shared resources on startup and release them on shutdown."""
    settings: Settings = app.state.settings
    app.state.engine = create_engine(settings)
    app.state.session_factory = create_session_factory(app.state.engine)
    app.state.redis = create_redis(settings)
    app.state.job_queue = JobQueue(settings)
    logger.info("API started env=%s version=%s", settings.app_env, __version__)
    try:
        yield
    finally:
        await app.state.job_queue.close()
        await app.state.redis.aclose()
        await app.state.engine.dispose()
        logger.info("API stopped")


async def _request_context_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Assign a request ID, log one line per request, and echo the ID in the response."""
    request_id = set_request_id(request.headers.get("x-request-id"))
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, elapsed_ms
    )
    response.headers["X-Request-ID"] = request_id
    return response


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application."""
    settings = settings or get_settings()
    setup_logging(SERVICE, settings)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=_lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    app.middleware("http")(_request_context_middleware)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


def run() -> None:
    """Console entry point: serve the API with uvicorn using our logging config."""
    settings = get_settings()
    uvicorn.run(
        "movie_companion.main:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env == "development",
        log_config=None,
    )
