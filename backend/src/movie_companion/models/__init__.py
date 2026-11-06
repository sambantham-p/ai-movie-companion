"""ORM models.

Import every model module here so `Base.metadata` is complete for Alembic autogenerate.
No domain tables exist yet; they arrive with their feature milestones (see the README roadmap).
"""

from movie_companion.db.base import Base

__all__ = ["Base"]
