# 🎬 Movie Companion

**Movie Companion** is an AI-powered movie discovery and theatre booking assistant designed to simplify the entire movie-going experience — from finding the right movie to choosing the best theatre seats.

It brings together movie ratings, audience reviews, theatre discovery, real-time seat availability, interactive 3D auditorium visualization, personalized seat recommendations, and human-assisted booking in one platform.

## Features

### Movie Discovery & Ratings
- Discover Tamil, English, and other movies.
- Explore movie details, genres, cast, trailers, and release information.
- Compare ratings from IMDb, TMDB, Rotten Tomatoes, and Metacritic where available.
- View a consolidated movie score with confidence indicators.

### AI-Powered Review Intelligence
- Analyze audience reviews and sentiment.
- Generate spoiler-aware summaries of positive and negative feedback.
- Identify commonly praised and criticized aspects of a movie.
- Provide review insights grounded in available audience feedback.

### Theatre Discovery
- Find nearby theatres and available movie shows.
- Explore premium experiences such as IMAX, EPIQ, Gold Class, and other formats.
- Browse theatres and screens by location, format, and preferences.
- Maintain personalized theatre collections.

### Smart Seat Selection & 3D Visualization
- Explore interactive 3D auditorium layouts.
- View seating arrangements and approximate screen perspectives.
- Evaluate seats based on viewing angles, screen alignment, distance, and group preferences.
- Receive personalized seat recommendations.

### Live Seat Availability & Alerts
- Check seat availability for supported shows.
- Monitor preferred seats and seating zones.
- Receive notifications when availability changes.
- Track seat availability through authorized browser sessions.

### Human-Assisted Booking
- Assist with navigating supported BookMyShow booking flows.
- Select preferred seats through user-authorized browser automation.
- Pause for manual intervention when authentication or verification is required.
- Hand control back to the user for payment and final confirmation.

### AI Movie Assistant
- Search for movies using natural language.
- Get personalized movie and theatre recommendations.
- Ask questions about ratings, reviews, shows, and seating options.
- Manage watch history, personal ratings, and seating preferences.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| Caching & Background Jobs | Redis, ARQ |
| Browser Automation | Playwright, Chrome CDP |
| 3D Visualization | Three.js, React Three Fiber |
| Testing & Quality | Pytest, Vitest, Ruff, mypy |
| Infrastructure | Docker Compose, GitHub Actions |

## Architecture

```text
                   Movie Companion
                          |
                    React Frontend
                          |
                     FastAPI API
                          |
             +------------+------------+
             |                         |
         PostgreSQL                  Redis
             |                         |
        Application              Background Jobs
           Data                        |
                            +----------+----------+
                            |                     |
                       Job Worker           Browser Worker
                                                  |
                                           Chrome Browser
                                                  |
                                             BookMyShow
```

The application separates frontend presentation, backend business logic, persistent data, background processing, and browser automation.

## Project Structure

```text
movie-companion/
├── backend/          # APIs, business logic, integrations
├── frontend/         # Web application and 3D experience
├── infra/            # Infrastructure configuration
├── scripts/          # Development utilities
├── .github/          # CI/CD workflows
├── Makefile          # Development commands
├── CLAUDE.md         # AI development instructions
└── README.md
```

## Prerequisites

- Python 3.12+
- uv
- Node.js 22+
- npm
- Docker and Docker Compose
- Google Chrome

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd movie-companion
```

Install project dependencies:

```bash
make setup
```

## Environment Configuration

Configure the required environment variables using the provided example files.

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Update the environment files with your database configuration, API credentials, and application settings.

Never commit secrets, authentication tokens, or browser profile data.

## Running the Application

Start infrastructure services:

```bash
make infra-up
```

Apply database migrations:

```bash
make migrate
```

Start the frontend:

```bash
make web
```

Start the backend:

```bash
make api
```

Start background workers when required:

```bash
make worker-jobs
make worker-browser
```

## Development & Testing

Run code quality checks:

```bash
make lint
```

Run security checks:

```bash
make security
```

Build the application:

```bash
make build
```

## Logging & Security

- Centralized application logging across backend services and workers.
- Environment-based configuration and secure credential management.
- Dedicated browser profiles for authorized browser automation.
- Human intervention for authentication, CAPTCHA, and payment.
- No CAPTCHA bypass, credential harvesting, or automated payment submission.
- Browser automation depends on supported page behavior and may be restricted by third-party platform terms.
