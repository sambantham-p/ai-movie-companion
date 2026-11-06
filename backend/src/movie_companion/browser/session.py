"""Lifecycle of the dedicated, persistent, user-authorized Chrome session.

Two modes (BROWSER_MODE):
- persistent: launch Chrome with a dedicated profile directory the user logged into once.
- cdp: attach to a Chrome the user started with --remote-debugging-port bound to 127.0.0.1.

All remote navigation goes through `goto`, which applies the allow-list and request budget.
This module never types credentials, OTPs or payment data, and never solves challenges.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from movie_companion.browser.policy import (
    RequestBudget,
    assert_navigation_allowed,
    is_local_url,
)
from movie_companion.core.config import Settings
from movie_companion.core.logging import get_logger

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, BrowserType, Page, Playwright

logger = get_logger(__name__)


def ensure_private_dir(path: Path) -> Path:
    """Create the profile directory readable only by the current user (mode 700)."""
    path.mkdir(parents=True, exist_ok=True)
    # Owner-only is the most restrictive mode; the rule's suggested 0o644 would expose the profile.
    # nosemgrep: python.lang.security.audit.insecure-file-permissions.insecure-file-permissions
    os.chmod(path, 0o700)
    return path


class BrowserSession:
    """Owns one Playwright instance and the user's browser context."""

    def __init__(self, settings: Settings, profile_dir: Path | None = None) -> None:
        self._settings = settings
        self._profile_dir = profile_dir or settings.browser_profile_dir
        self.budget = RequestBudget(settings.browser_max_page_loads_per_hour)
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    @property
    def context(self) -> BrowserContext:
        """The active browser context; raises if the session is not started."""
        if self._context is None:
            raise RuntimeError("Browser session is not started")
        return self._context

    async def start(self) -> None:
        """Start Playwright and open (or attach to) the user's browser context."""
        from playwright.async_api import async_playwright  # optional dependency

        self._playwright = await async_playwright().start()
        try:
            await self._open_context(self._playwright.chromium)
        except BaseException:
            # Don't leak the Playwright driver or a CDP attachment to the owner's Chrome when
            # start fails partway; callers shouldn't have to remember to stop() a failed start.
            # A cleanup failure is logged, never raised, so the real startup error surfaces.
            try:
                await self.stop()
            except Exception:
                logger.warning("Cleanup after failed browser start also failed", exc_info=True)
            raise

    async def _open_context(self, chromium: BrowserType) -> None:
        """Attach over CDP or launch the persistent profile; sets the browser context."""
        if self._settings.browser_mode == "cdp":
            self._browser = await chromium.connect_over_cdp(self._settings.browser_cdp_url)
            if not self._browser.contexts:
                raise RuntimeError("Attached Chrome has no browser context")
            self._context = self._browser.contexts[0]
            logger.info("Attached to Chrome over CDP")
        else:
            profile = ensure_private_dir(self._profile_dir)
            launch_args: dict[str, Any] = {"headless": self._settings.browser_headless}
            if self._settings.browser_channel == "chrome":
                launch_args["channel"] = "chrome"
            self._context = await chromium.launch_persistent_context(str(profile), **launch_args)
            logger.info(
                "Launched %s with persistent profile (headless=%s)",
                self._settings.browser_channel,
                self._settings.browser_headless,
            )

    async def new_page(self) -> Page:
        """Open a new tab in the user's context."""
        return await self.context.new_page()

    async def goto(self, page: Page, url: str) -> None:
        """Navigate after enforcing the allow-list and (for remote pages) the budget."""
        assert_navigation_allowed(url)
        if is_local_url(url):
            await page.goto(url)
            return
        async with self.budget.lock:
            self.budget.consume()
            await page.goto(url, wait_until="domcontentloaded")

    def browser_version(self) -> str:
        """Version string of the running browser, if known."""
        browser = self._context.browser if self._context else None
        return browser.version if browser else "unknown"

    async def stop(self) -> None:
        """Close the context (persistent mode) or detach (CDP mode), then stop Playwright."""
        try:
            if self._settings.browser_mode == "cdp":
                if self._browser is not None:
                    await self._browser.close()  # detaches; the user's Chrome keeps running
            elif self._context is not None:
                await self._context.close()
        finally:
            if self._playwright is not None:
                await self._playwright.stop()
            self._context = self._browser = self._playwright = None
            logger.info("Browser session stopped")
