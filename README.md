# Leaderboard REST API

FastAPI backend for the Aim Trainer leaderboard.

## Setup

1. Copy `.env.example` to `.env` and fill in your PostgreSQL settings.
2. Make sure PostgreSQL is running and the target database exists.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

Recommended:

```bash
python -m api.run
```

Alternative:

```bash
python -m uvicorn api.main:app --reload
```

If the database tables or seed data are missing, the app will prompt in the terminal on startup and can initialize them automatically from [api/database/schema.sql](api/database/schema.sql) and [api/database/seed.sql](api/database/seed.sql).

## Docker

Start API + PostgreSQL together:

```bash
docker compose up --build
```

Available services:

- API: http://localhost:8000
- Health check: http://localhost:8000/health
- PostgreSQL: localhost:5432

Container startup behavior:

- the API waits for PostgreSQL readiness
- schema and seed are initialized automatically when missing (`AUTO_INIT_DB=true`)

Stop and remove containers:

```bash
docker compose down
```

Also remove the PostgreSQL volume (fresh DB state):

```bash
docker compose down -v
```

## Auth

The API includes basic JWT authentication:

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `PUT /player/{username}`

Set `JWT_SECRET` in your local `.env` before using auth in anything beyond development.

## Database files

The SQL files in [api/database](api/database) are still needed for initial setup:

- [schema.sql](api/database/schema.sql)
- [seed.sql](api/database/seed.sql)

They are not required on every startup once the database is initialized.

## Leaderboard queries

The leaderboard supports:

- ranking by `score`, `accuracy`, `hits`, `misses`, or `date`
- filtering by player, mode, date range, and score range
- player-specific, mode-specific, and date-specific endpoints under `/leaderboard`
