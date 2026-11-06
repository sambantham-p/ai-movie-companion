"""Alembic migration environment (async).

Reads the database URL from application settings and the target metadata from
`movie_companion.models`, so migrations always match the ORM and the configured database.
"""

from __future__ import annotations

import asyncio

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from movie_companion.core.config import get_settings
from movie_companion.core.logging import setup_logging
from movie_companion.models import Base

settings = get_settings()
setup_logging("migrations", settings)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a database connection (`alembic upgrade --sql`)."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_sync(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations against the configured database."""
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as connection:
        await connection.run_sync(_run_sync)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
