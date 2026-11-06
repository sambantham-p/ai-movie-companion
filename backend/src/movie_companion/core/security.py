"""Owner authentication for the single-user API.

Every non-health route depends on `require_owner`, which checks a bearer token against
OWNER_API_TOKEN in constant time. In development an unset token disables the check (with a
warning); production refuses to start without one (see `Settings`).
"""

from __future__ import annotations

import hmac

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from movie_companion.core.config import Settings, get_settings
from movie_companion.core.errors import UnauthorizedError
from movie_companion.core.logging import get_logger

logger = get_logger(__name__)
_bearer = HTTPBearer(auto_error=False)
_warned_open = False


async def require_owner(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> None:
    """Reject the request unless it carries the owner's bearer token."""
    global _warned_open
    expected = settings.owner_api_token
    if expected is None:
        if not _warned_open:
            logger.warning("OWNER_API_TOKEN is not set: API auth is disabled (development only)")
            _warned_open = True
        return
    supplied = credentials.credentials if credentials else ""
    if not hmac.compare_digest(supplied.encode(), expected.get_secret_value().encode()):
        raise UnauthorizedError("Missing or invalid API token")
