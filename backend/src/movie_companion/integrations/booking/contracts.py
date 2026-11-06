"""Contracts for seat sources and booking providers.

These types are the only shape the rest of the app sees for live seats and bookings. They
encode two product rules from the research:
- Availability is binary as observed (open / unavailable); "sold vs held vs blocked" is unknown.
- A snapshot is "live" only while it is fresh; stale data must never be presented as live.

Implementations (browser reader, extension, deep-link-only booking) arrive in later milestones.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Protocol

# A snapshot older than this is shown as "as of <time>", never as live availability.
LIVE_SNAPSHOT_MAX_AGE = timedelta(seconds=90)


class SeatAvailability(StrEnum):
    """What the booking page shows for a seat."""

    OPEN = "open"
    UNAVAILABLE = "unavailable"  # sold, held by someone, or blocked: indistinguishable


@dataclass(frozen=True, slots=True)
class ObservedSeat:
    """One seat as read from the provider's seat map."""

    row_label: str
    seat_number: str
    grid_x: int
    grid_y: int
    category: str
    price_minor: int | None
    availability: SeatAvailability


@dataclass(frozen=True, slots=True)
class SeatSnapshot:
    """All seats of one show at one moment."""

    provider: str
    show_ref: str
    captured_at: datetime
    seats: tuple[ObservedSeat, ...]
    content_hash: str

    def age(self, now: datetime | None = None) -> timedelta:
        """How old this snapshot is."""
        return (now or datetime.now(UTC)) - self.captured_at

    def is_live(self, now: datetime | None = None) -> bool:
        """True only while fresh enough to label as live availability."""
        return self.age(now) <= LIVE_SNAPSHOT_MAX_AGE


class SeatSource(Protocol):
    """Reads the current seat map for a show."""

    provider: str

    async def read_show(self, show_ref: str) -> SeatSnapshot:
        """Return a fresh snapshot or raise; never return cached data from here."""
        ...


class BookingRunState(StrEnum):
    """States of a human-in-the-loop booking run. `PAUSED_*` states wait for the user."""

    QUEUED = "queued"
    RUNNING = "running"
    PAUSED_LOGIN = "paused_login"
    PAUSED_OTP = "paused_otp"
    PAUSED_CAPTCHA = "paused_captcha"
    PAUSED_UNKNOWN_SCREEN = "paused_unknown_screen"
    PAUSED_SEATS_TAKEN = "paused_seats_taken"
    AWAITING_PAYMENT = "awaiting_payment"  # hard stop: the user pays, never the agent
    CONFIRMED = "confirmed"  # only after the provider's confirmation page is observed
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class BookingRequest:
    """What the user asked the agent to hold."""

    provider: str
    show_ref: str
    party_size: int
    preferred_seats: list[str] = field(default_factory=list)


class BookingProvider(Protocol):
    """Drives a booking up to, and never past, the payment page."""

    provider: str

    async def start(self, request: BookingRequest) -> str:
        """Start a run and return its ID."""
        ...

    async def resume(self, run_id: str) -> BookingRunState:
        """Continue a paused run after the user finished the manual step."""
        ...
