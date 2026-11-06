"""Adapters to external systems (TMDB, OMDb, Google Places, LLMs, Telegram, BookMyShow).

Each integration sits behind a small interface so the rest of the app never depends on a
provider's wire format, and unavailable providers can be swapped or clearly mocked.
"""
