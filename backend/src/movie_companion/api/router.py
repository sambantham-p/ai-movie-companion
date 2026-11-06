"""Version-1 API router. Feature routers are included here; protected ones depend on the owner."""

from __future__ import annotations

from fastapi import APIRouter

from movie_companion.api.routes import health

api_router = APIRouter()

# Public
api_router.include_router(health.router)

# Protected feature routers are added as milestones land, e.g.:
# api_router.include_router(movies.router, dependencies=[Depends(require_owner)])
