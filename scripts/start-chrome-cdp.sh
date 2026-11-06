#!/usr/bin/env bash
# Start Google Chrome with the dedicated Movie Companion profile and a DevTools port bound to
# 127.0.0.1 only, for BROWSER_MODE=cdp. Log in to BookMyShow yourself in this window.
# Never expose this port to a network: anyone who can reach it controls the logged-in browser.
set -euo pipefail

PROFILE_DIR="${BROWSER_PROFILE_DIR:-$HOME/.movie-companion/chrome-profile}"
PORT="${BROWSER_CDP_PORT:-9222}"

mkdir -p "$PROFILE_DIR"
chmod 700 "$PROFILE_DIR"

case "$(uname -s)" in
  Darwin) CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ;;
  *) CHROME="$(command -v google-chrome || command -v google-chrome-stable || command -v chromium)" ;;
esac

if [[ ! -x "$CHROME" ]]; then
  echo "Google Chrome not found. Install it, or use BROWSER_MODE=persistent." >&2
  exit 1
fi

echo "Starting Chrome (profile: $PROFILE_DIR, DevTools on 127.0.0.1:$PORT)"
exec "$CHROME" \
  --user-data-dir="$PROFILE_DIR" \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port="$PORT" \
  --no-first-run \
  --no-default-browser-check
