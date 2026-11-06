"""Navigation policy and request budget for the browser worker.

Enforces the BookMyShow boundaries agreed in the research (see README, "Security notes"):
- The browser may only navigate to allow-listed hosts (plus local about:/data: pages).
- Page loads are capped by a sliding one-hour budget and run one at a time.
- Exceeding the budget raises instead of waiting, so callers back off visibly.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from urllib.parse import urlsplit

from movie_companion.core.errors import PolicyViolationError

ALLOWED_HOSTS: frozenset[str] = frozenset({"in.bookmyshow.com", "bookmyshow.com"})
LOCAL_SCHEMES: frozenset[str] = frozenset({"about", "data"})


def is_local_url(url: str) -> bool:
    """True for local pages (about:, data:) that never touch the network or the budget."""
    try:
        return urlsplit(url).scheme.lower() in LOCAL_SCHEMES
    except ValueError:
        return False


def is_navigation_allowed(url: str) -> bool:
    """True if the worker may load this URL. Malformed or ambiguous URLs are refused."""
    try:
        if is_local_url(url):
            return True
        parts = urlsplit(url)
    except ValueError:
        return False
    # Python's urlsplit and Chrome's WHATWG parser disagree on backslashes and userinfo:
    # "https://evil.com\@in.bookmyshow.com/" looks allow-listed here but Chrome opens evil.com.
    # Real BookMyShow URLs never need either, so refuse them (and control characters) outright.
    if "\\" in url or parts.username is not None or any(ord(c) < 0x20 for c in url):
        return False
    return parts.scheme == "https" and (parts.hostname or "").lower() in ALLOWED_HOSTS


def assert_navigation_allowed(url: str) -> None:
    """Raise PolicyViolationError for any URL outside the allow-list."""
    if not is_navigation_allowed(url):
        raise PolicyViolationError(f"Navigation to '{url[:60]}' is not allowed by browser policy")


class BudgetExceededError(PolicyViolationError):
    """The hourly page-load budget is used up."""

    code = "browser_budget_exceeded"


class RequestBudget:
    """Sliding-window limit on remote page loads, serialised so only one runs at a time."""

    WINDOW_SECONDS = 3600.0

    def __init__(self, max_per_hour: int) -> None:
        self.max_per_hour = max_per_hour
        self._stamps: deque[float] = deque()
        self.lock = asyncio.Lock()

    def _prune(self, now: float) -> None:
        while self._stamps and now - self._stamps[0] >= self.WINDOW_SECONDS:
            self._stamps.popleft()

    def remaining(self, now: float | None = None) -> int:
        """Page loads still available in the current window."""
        self._prune(now if now is not None else time.monotonic())
        return self.max_per_hour - len(self._stamps)

    def consume(self, now: float | None = None) -> None:
        """Record one page load or raise BudgetExceededError."""
        now = now if now is not None else time.monotonic()
        self._prune(now)
        if len(self._stamps) >= self.max_per_hour:
            raise BudgetExceededError(
                f"Browser budget of {self.max_per_hour} page loads/hour reached; backing off"
            )
        self._stamps.append(now)
