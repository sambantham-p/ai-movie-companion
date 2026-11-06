"""Async engine and session factory.

The engine is created once per process (in the API lifespan or a worker's startup) and
disposed on shutdown. Request handlers get a session through `get_session`, which commits
on success and rolls back on any exception.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from movie_companion.core.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Build the process-wide async engine."""
    return create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build a session factory bound to the engine."""
    return async_sessionmaker(engine, expire_on_commit=False)


async def ping_database(engine: AsyncEngine) -> None:
    """Run a trivial query; raises if the database is unreachable."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a transactional session for one request."""
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
