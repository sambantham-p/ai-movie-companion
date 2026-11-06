"""Per-request context shared with logging.

A context variable carries the request ID so every log line written while handling a
request (or a job) can be correlated without passing IDs through function arguments.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    """Return the current request/job ID, or '-' outside a request."""
    return _request_id.get()


def set_request_id(value: str | None = None) -> str:
    """Set the current request ID (generating one if absent) and return it."""
    request_id = value or uuid.uuid4().hex[:16]
    _request_id.set(request_id)
    return request_id
