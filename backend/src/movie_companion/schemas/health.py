"""Response schemas for liveness and readiness endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

CheckStatus = Literal["ok", "error"]


class LivenessResponse(BaseModel):
    """The API process is up."""

    status: Literal["ok"] = "ok"
    service: str
    version: str
    environment: str


class DependencyCheck(BaseModel):
    """Result of checking one dependency."""

    status: CheckStatus
    latency_ms: float | None = None
    error: str | None = None


class WorkerStatus(BaseModel):
    """Heartbeat state of one background worker."""

    online: bool
    last_seen: datetime | None = None


class ReadinessResponse(BaseModel):
    """Dependencies needed to serve traffic, plus informational worker status."""

    status: Literal["ready", "not_ready"]
    database: DependencyCheck
    redis: DependencyCheck
    # Workers don't gate readiness: the browser worker lives on a home machine that may sleep.
    workers: dict[str, WorkerStatus]
