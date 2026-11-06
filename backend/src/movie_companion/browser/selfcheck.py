"""Browser environment self-check.

Launches Chrome through the same session code the worker uses, loads a local data: page,
and exits. It never contacts BookMyShow or any remote site. By default it uses a throwaway
profile so it cannot disturb the real logged-in profile.

Usage: `uv run python -m movie_companion.browser.selfcheck [--headed] [--use-real-profile]`
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import tempfile
from pathlib import Path

from movie_companion.browser.session import BrowserSession
from movie_companion.core.config import get_settings
from movie_companion.core.logging import get_logger, setup_logging

logger = get_logger(__name__)
_TEST_PAGE = "data:text/html,<title>movie-companion-selfcheck</title><p>ok</p>"


async def run_selfcheck(headed: bool, use_real_profile: bool) -> bool:
    """Start a session, load a local page, verify its title, stop. Returns success."""
    update: dict[str, object] = {"browser_headless": not headed}
    if not use_real_profile:
        # BROWSER_MODE=cdp would attach to the owner's logged-in Chrome and ignore the throwaway
        # profile, so the isolated check always launches its own persistent context.
        update["browser_mode"] = "persistent"
    settings = get_settings().model_copy(update=update)
    # Only the isolated check needs a throwaway profile. Chrome helpers (e.g. crashpad) can still
    # be writing into it right after shutdown, so cleanup errors must not fail a good check.
    temp_dir = (
        contextlib.nullcontext(None)
        if use_real_profile
        else tempfile.TemporaryDirectory(prefix="mc-selfcheck-", ignore_cleanup_errors=True)
    )
    with temp_dir as tmp:
        profile = Path(tmp) / "profile" if tmp else None
        session = BrowserSession(settings, profile_dir=profile)
        page = None
        try:
            await session.start()
            page = await session.new_page()
            await session.goto(page, _TEST_PAGE)
            title = await page.title()
            # Annotated: without the optional Playwright install, `title` is untyped (Any).
            ok: bool = title == "movie-companion-selfcheck"
            logger.info("Self-check browser=%s title_ok=%s", session.browser_version(), ok)
            return ok
        finally:
            # In CDP mode stop() only detaches, so close our tab or it stays in the owner's Chrome.
            # Best effort: a tab that is already gone must not mask the real result or error.
            if page is not None:
                try:
                    await page.close()
                except Exception:
                    logger.warning("Self-check could not close its tab", exc_info=True)
            try:
                await session.stop()
            except Exception:
                logger.warning("Self-check could not stop the browser session", exc_info=True)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").partition("\n")[0])
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    parser.add_argument(
        "--use-real-profile",
        action="store_true",
        help=(
            "use BROWSER_PROFILE_DIR instead of a temp one "
            "(stop the browser worker first: Chrome locks a profile to one process)"
        ),
    )
    args = parser.parse_args()
    setup_logging("browser")
    ok = asyncio.run(run_selfcheck(args.headed, args.use_real_profile))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
