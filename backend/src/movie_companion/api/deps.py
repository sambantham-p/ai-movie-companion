"""Shared FastAPI dependencies that expose process-wide resources to routes."""

from __future__ import annotations

from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine

from movie_companion.jobs.client import JobQueue


def get_engine(request: Request) -> AsyncEngine:
    """Return the database engine created in the app lifespan."""
    engine: AsyncEngine = request.app.state.engine
    return engine


def get_redis(request: Request) -> Redis:
    """Return the shared Redis client."""
    redis: Redis = request.app.state.redis
    return redis


def get_job_queue(request: Request) -> JobQueue:
    """Return the ARQ producer used to hand work to the workers."""
    queue: JobQueue = request.app.state.job_queue
    return queue
