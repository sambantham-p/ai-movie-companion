"""Queue names and heartbeat timing shared by producers and both workers."""

from __future__ import annotations

from typing import Final

JOBS_QUEUE: Final = "mc:queue:jobs"
BROWSER_QUEUE: Final = "mc:queue:browser"

# Workers refresh their heartbeat every minute; a missing key after the TTL means offline.
HEARTBEAT_TTL_SECONDS: Final = 180
