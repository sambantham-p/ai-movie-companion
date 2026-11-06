"""User-authorized browser worker (runs only on the owner's home machine).

Owns the dedicated Chrome profile, enforces the navigation policy and request budget, and
consumes the `browser` queue. Requires the `browser` extra: `uv sync --extra browser`.
"""
