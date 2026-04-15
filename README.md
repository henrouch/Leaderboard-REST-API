# Leaderboard REST API

FastAPI backend for the Aim Trainer leaderboard.

## Setup

1. Copy `.env.example` to `.env` and fill in your PostgreSQL settings.
2. Make sure PostgreSQL is running and the target database exists.
3. Install dependencies:

```bash
pip install fastapi psycopg2-binary uvicorn
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

If the database tables or seed data are missing, the app will prompt in the terminal on startup and can initialize them automatically.

## Database files

The SQL files in [api/database](api/database) are still needed for initial setup:

- [schema.sql](api/database/schema.sql)
- [seed.sql](api/database/seed.sql)

They are not required on every startup once the database is initialized.
