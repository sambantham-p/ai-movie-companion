"""Background jobs run by ARQ workers.

Two queues exist: `jobs` (cloud-safe work: data sync, scoring, alerts) and `browser`
(user-authorized browser work, consumed only by the home-machine browser worker).
"""
