"""Application error types and the API's error envelope.

Services raise `AppError` subclasses; the handlers registered here turn them into a single
JSON shape: {"error": {"code", "message", "request_id", "details"?}}. Unexpected exceptions
are logged once with a stack trace and returned as a generic 500.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from movie_companion.core.logging import get_logger
from movie_companion.core.request_context import get_request_id

logger = get_logger(__name__)


class AppError(Exception):
    """Base class for expected, user-facing errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "bad_request"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(AppError):
    """A requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    """The request conflicts with current state."""

    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class UnauthorizedError(AppError):
    """Missing or invalid credentials."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"


class ExternalServiceError(AppError):
    """A third-party provider failed or returned something unusable."""

    status_code = status.HTTP_502_BAD_GATEWAY
    code = "external_service_error"


class PolicyViolationError(AppError):
    """An action would break a product boundary (e.g. the BookMyShow automation policy)."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "policy_violation"


def _envelope(code: str, message: str, details: Any = None) -> dict[str, Any]:
    body: dict[str, Any] = {"code": code, "message": message, "request_id": get_request_id()}
    if details is not None:
        body["details"] = details
    return {"error": body}


async def _handle_app_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    log = logger.error if exc.status_code >= 500 else logger.info
    log("AppError code=%s status=%s message=%s", exc.code, exc.status_code, exc.message)
    return JSONResponse(
        status_code=exc.status_code, content=_envelope(exc.code, exc.message, exc.details)
    )


async def _handle_validation_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    # Strip submitted input from the details so request bodies never echo back secrets.
    details = [
        {"loc": e.get("loc"), "msg": e.get("msg"), "type": e.get("type")} for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=_envelope("validation_error", "Request validation failed", details),
    )


_HTTP_CODES = {404: "not_found", 405: "method_not_allowed", 401: "unauthorized", 403: "forbidden"}


async def _handle_http_exception(_: Request, exc: Exception) -> JSONResponse:
    """Wrap framework HTTP errors (unknown route, wrong method) in the same envelope."""
    assert isinstance(exc, StarletteHTTPException)
    code = _HTTP_CODES.get(exc.status_code, "http_error")
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(code, str(exc.detail)),
        headers=getattr(exc, "headers", None),
    )


async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_envelope("internal_error", "Something went wrong. Check the server logs."),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the error handlers to the FastAPI app."""
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(Exception, _handle_unexpected)
