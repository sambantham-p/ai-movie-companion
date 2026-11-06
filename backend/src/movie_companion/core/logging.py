"""Centralized logging for every backend process.

Call `setup_logging(service)` once at process start (API, jobs worker, browser worker), then
use `get_logger(__name__)` everywhere. Never configure handlers in individual modules.

Guarantees:
- One format: timestamp | level | logger | request id | message.
- Console output plus a rotating file per service (`logs/<service>.log`).
- Every formatted line, including tracebacks, passes through secret redaction.
"""

from __future__ import annotations

import logging
import logging.config
import re
from typing import Any

from movie_companion.core.config import Settings, get_settings
from movie_companion.core.request_context import get_request_id

LOG_FORMAT = (
    "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s | req=%(request_id)s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Key/value pairs whose value must never reach a log: key=value, key: value, "key": "value".
_SENSITIVE_KEYS = (
    r"password|passwd|pwd|secret|token|api[_-]?key|apikey|authorization|cookie|"
    r"set-cookie|session(?:id)?|otp|cvv|card(?:_?number)?|upi(?:_?id)?|private[_-]?key"
)
_KV_PATTERN = re.compile(
    rf"(?i)([\"']?(?:{_SENSITIVE_KEYS})[\"']?\s*[:=]\s*[\"']?)([^\s\"',;&}}]+)"
)
_BEARER_PATTERN = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+")
_URL_CREDENTIALS_PATTERN = re.compile(r"(://[^:/@\s]+:)[^@\s]+(@)")
_TELEGRAM_TOKEN_PATTERN = re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b")

REDACTED = "***"


def redact(text: str) -> str:
    """Mask credentials, tokens, OTPs and similar secrets in a log string."""
    text = _BEARER_PATTERN.sub(rf"\1{REDACTED}", text)
    text = _URL_CREDENTIALS_PATTERN.sub(rf"\1{REDACTED}\2", text)
    text = _TELEGRAM_TOKEN_PATTERN.sub(REDACTED, text)
    return _KV_PATTERN.sub(rf"\1{REDACTED}", text)


class RequestContextFilter(logging.Filter):
    """Attach the current request/job ID to every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class RedactingFormatter(logging.Formatter):
    """Formatter that redacts secrets from the fully formatted line, tracebacks included."""

    def format(self, record: logging.LogRecord) -> str:
        return redact(super().format(record))


def _build_config(service: str, settings: Settings) -> dict[str, Any]:
    """Build the dictConfig for one process."""
    handlers: dict[str, dict[str, Any]] = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "filters": ["request_context"],
            "stream": "ext://sys.stderr",
        }
    }
    if settings.log_to_file:
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            # One file per service avoids rotation races between processes.
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "filters": ["request_context"],
            "filename": str(settings.log_dir / f"{service}.log"),
            "maxBytes": settings.log_file_max_bytes,
            "backupCount": settings.log_file_backup_count,
            "encoding": "utf-8",
        }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_context": {"()": RequestContextFilter}},
        "formatters": {
            "standard": {"()": RedactingFormatter, "format": LOG_FORMAT, "datefmt": DATE_FORMAT}
        },
        "handlers": handlers,
        "root": {"level": settings.log_level, "handlers": list(handlers)},
        "loggers": {
            # Route third-party loggers through the root handlers; quiet the noisy ones.
            "uvicorn": {"handlers": [], "propagate": True},
            "uvicorn.error": {"handlers": [], "propagate": True},
            "uvicorn.access": {"handlers": [], "propagate": True, "level": "WARNING"},
            "sqlalchemy.engine": {"level": "INFO" if settings.database_echo else "WARNING"},
            "arq": {"level": "INFO"},
            "httpx": {"level": "WARNING"},
            "httpcore": {"level": "WARNING"},
            "asyncio": {"level": "WARNING"},
        },
    }


def setup_logging(service: str, settings: Settings | None = None) -> None:
    """Configure logging for this process. `service` names the log file (api, jobs, browser)."""
    settings = settings or get_settings()
    logging.config.dictConfig(_build_config(service, settings))
    logging.captureWarnings(True)
    get_logger(__name__).debug("Logging configured for service=%s", service)


def get_logger(name: str) -> logging.Logger:
    """Return a module logger. Use `get_logger(__name__)`."""
    return logging.getLogger(name)
