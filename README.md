# Movie Companion

A personal AI movie companion: discover genuinely good Tamil and English films, understand real
audience opinion, find the best nearby screen, see exactly what a seat looks like in 3D, get
warned before good seats run out, and let an agent carry the booking up to the payment page.

> **Status:** Phase 0 — project foundation. The stack, structure, logging, database, workers,
> browser lifecycle, health checks, tests and CI are in place. Product features are built
> phase by phase (see [Roadmap](#16-development-roadmap)).

## 1. Problem

Deciding on a film means checking IMDb, Reddit and review sites, comparing theatres and
showtimes, and hunting for a good seat — often after the best seats are gone. Movie Companion
puts that whole flow in one place.

## 2. Features and capabilities

| Area | What it does |
|---|---|
| Movie discovery | Recent Tamil and English releases, genres, global search |
| Rating intelligence | IMDb, TMDB, Rotten Tomatoes and Metacritic combined into one vote-weighted score with confidence |
| AI review intelligence | Structured audience sentiment from real reviews; never invented |
| Theatre discovery | Location-based cinemas, premium collection first (per screen format) |
| Live seat availability | Real seat maps from your own logged-in BookMyShow session, always time-stamped |
| Seat scoring | Viewing-angle based seat scores (SMPTE/THX), centrality, comfort, adjacency |
| 3D auditorium | Interactive seats, view-from-seat camera, walk-in animation |
| Seat monitoring + alerts | Telegram / web push when your preferred seats start running out or come back |
| Assisted booking | Agent drives the booking, pauses for login/OTP/CAPTCHA, stops before payment |
| AI assistant & watch history | Natural-language discovery; your ratings and seat feedback |

BookMyShow has no public API. Live seats and booking use **user-authorized automation of your
own account in your own Chrome on your own home connection**, with strict limits. No
CAPTCHA/OTP/anti-bot bypassing; payment is always manual.

## 3. Technology stack

| Layer | Choice |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic v2, uvicorn, uv |
| Database | PostgreSQL 16, SQLAlchemy 2 (async, asyncpg), Alembic |
| Jobs & cache | Redis 7, ARQ (two queues: `jobs`, `browser`) |
| Browser automation | Playwright driving Google Chrome with a dedicated persistent profile (or CDP attach) |
| Frontend | React 19, TypeScript, Vite, React Router, TanStack Query, Zustand, Tailwind CSS v4 |
| 3D | React Three Fiber + drei (three.js) |
| Notifications (later) | Telegram Bot API, Web Push (VAPID), email |
| LLM (later) | Provider-agnostic adapter (Anthropic / OpenAI / Gemini) |
| Quality | pytest + pytest-cov, ruff, mypy strict · Vitest + Testing Library + V8 coverage, oxlint, Prettier · ≥ 85% coverage gates |
| Infra | Docker Compose (local Postgres/Redis), GitHub Actions CI |


## 4. Architecture

```
React SPA ──HTTP──> FastAPI ──> PostgreSQL
                      │  └────> Redis (cache, heartbeats)
                      └─enqueue─> Redis queues
                                   ├─ jobs queue    → jobs worker     (data sync, scoring, alerts)
                                   └─ browser queue → browser worker  (home machine only)
                                                        └─ your Chrome profile → BookMyShow
```

One Python package runs as three processes. Only the browser worker ever talks to BookMyShow,
and it runs on your own machine so it uses your IP and logged-in profile. It connects outward to
Redis, so nothing on your machine is exposed to the internet.

## 5. Repository structure

```
backend/        FastAPI app, workers, browser automation, Alembic migrations
frontend/       React + Vite SPA
infra/          docker-compose.yml for Postgres and Redis
scripts/        start-chrome-cdp.sh
.github/        CI workflow (lint, type-check, security scans, build)
Makefile        All commands — run `make help`
```

## 6. Prerequisites

- macOS or Linux
- Python 3.12 and [uv](https://docs.astral.sh/uv/) (`brew install uv`)
- Node.js 22+ and npm
- Docker Desktop **or** local Postgres 16 + Redis 7 (`brew install postgresql@16 redis`)
- Google Chrome (for the browser worker)

## 7. Installation

```bash
make setup   # uv sync (with Playwright), npm ci, and creates backend/.env + frontend/.env.local
```

## 8. Environment setup

- `backend/.env` — from `backend/.env.example`. Defaults work for local development.
  Set `OWNER_API_TOKEN` (required in production):
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `frontend/.env.local` — from `frontend/.env.example`. `VITE_*` values are public; no secrets.
- Integration keys (TMDB, OMDb, Google Maps, YouTube, LLM, Telegram, VAPID) are only needed from
  the phases that use them.

## 9. Database and infrastructure

With Docker:

```bash
make infra-up    # Postgres on 127.0.0.1:5432, Redis on 127.0.0.1:6379 (+ test database)
make migrate     # apply Alembic migrations
make infra-down  # stop (data kept); `make infra-reset` deletes data
```

Without Docker (Homebrew):

```bash
brew services start postgresql@16 && brew services start redis
psql postgres -c "CREATE ROLE movie LOGIN PASSWORD 'movie';"
psql postgres -c "CREATE DATABASE movie_companion OWNER movie;"
psql postgres -c "CREATE DATABASE movie_companion_test OWNER movie;"
make migrate
```

New migration: `make migration m="add movies table"` (then review the generated file).

## 10. Run the frontend

```bash
make web   # http://localhost:5173 — proxies /api to the backend
```

## 11. Run the backend

```bash
make api           # http://127.0.0.1:8000, docs at /docs (development only)
make worker-jobs   # cloud-safe background jobs
curl http://127.0.0.1:8000/api/v1/health         # liveness
curl http://127.0.0.1:8000/api/v1/health/ready   # Postgres, Redis, worker heartbeats
```

## 12. Run the browser worker (home machine)

```bash
make browser-selfcheck   # opens Chrome on a local test page and closes it; never visits BookMyShow
make worker-browser      # starts Chrome with the dedicated profile and consumes the browser queue
```

- Profile: `~/.movie-companion/chrome-profile` (outside the repo, mode 700). Log in to
  BookMyShow yourself in that window once, when the live-seat phase begins.
- Attach mode: `make chrome-cdp`, then set `BROWSER_MODE=cdp` in `backend/.env`. The DevTools
  port listens on 127.0.0.1 only — never expose it.
- No booking or seat-reading jobs exist yet; they arrive in phases 5–7.

## 13. Quality checks

```bash
make lint               # ruff, mypy, oxlint, prettier, tsc
make security           # Semgrep, gitleaks, pip-audit, npm audit (free, open source)
make build              # production frontend build
```

The test suites (≥ 85% coverage on both sides, never contacting BookMyShow) are maintained
privately and are not part of this repository.

## 14. Logging

Backend logs go to the console and to rotating files in `backend/logs/<service>.log`
(`api`, `jobs`, `browser`, `migrations`), with request IDs and automatic secret redaction.
Frontend uses `createLogger()` from `src/lib/logger.ts`.

## 15. Security notes

Single-owner app protected by `OWNER_API_TOKEN`. Secrets live only in `.env` files (git-ignored).
Browser profiles, captures and HAR files are git-ignored and never served. Remote access to the
agent's browser must sit behind Tailscale or Cloudflare Access.

## 16. Development roadmap

| Phase | Scope | Status |
|---|---|---|
| 0 | Foundation | Done |
| 1 | Movie discovery, search, combined score | Next |
| 2 | Review intelligence | Planned |
| 3 | Theatre discovery, premium collections, deep links | Planned |
| 4 | Seat scoring, 3D auditorium, perspective view | Planned |
| 5 | Live seat reader (read-only) | Planned |
| 6 | Seat monitoring and alerts | Planned |
| 7 | Human-in-the-loop booking agent | Planned |
| 8 | AI assistant, watch history, hardening | Planned |
