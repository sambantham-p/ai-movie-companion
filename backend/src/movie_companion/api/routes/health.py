"""Liveness and readiness endpoints. Public by design: they expose no data."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine

from movie_companion import __version__
from movie_companion.api.deps import get_engine, get_redis
from movie_companion.core.config import Settings, get_settings
from movie_companion.schemas.health import LivenessResponse, ReadinessResponse
from movie_companion.services.health import check_readiness

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=LivenessResponse)
async def liveness(settings: Settings = Depends(get_settings)) -> LivenessResponse:  # noqa: B008
    """The process is running. Does not touch dependencies."""
    return LivenessResponse(
        service=settings.app_name, version=__version__, environment=settings.app_env
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness(
    response: Response,
    engine: AsyncEngine = Depends(get_engine),  # noqa: B008
    redis: Redis = Depends(get_redis),  # noqa: B008
) -> ReadinessResponse:
    """Postgres and Redis are reachable; also reports worker heartbeats. 503 when not ready."""
    result = await check_readiness(engine, redis)
    if result.status != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
