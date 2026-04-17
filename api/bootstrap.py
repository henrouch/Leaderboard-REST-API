from __future__ import annotations

import os
from pathlib import Path
import time
import sys

from api.db import get_connection


REQUIRED_TABLES = ("users", "game_modes", "game_results")
BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
SCHEMA_FILE = DATABASE_DIR / "schema.sql"
SEED_FILE = DATABASE_DIR / "seed.sql"


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _wait_for_database() -> None:
    timeout_seconds = int(os.getenv("DB_WAIT_TIMEOUT_SECONDS", "60"))
    interval_seconds = float(os.getenv("DB_WAIT_INTERVAL_SECONDS", "1"))
    deadline = time.monotonic() + max(0, timeout_seconds)
    last_error: Exception | None = None

    while time.monotonic() <= deadline:
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            return
        except Exception as exc:  # pragma: no cover - runtime environment dependent
            last_error = exc
            time.sleep(interval_seconds)

    raise RuntimeError(
        f"Database was not reachable within {timeout_seconds} seconds."
    ) from last_error


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute("SELECT to_regclass(%s)", (f"public.{table_name}",))
    row = cursor.fetchone()
    return bool(row and row[0])


def _modes_seeded(cursor) -> bool:
    cursor.execute("SELECT COUNT(*) FROM game_modes")
    row = cursor.fetchone()
    return bool(row and row[0] > 0)


def database_ready() -> bool:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            if not all(
                _table_exists(cursor, table_name) for table_name in REQUIRED_TABLES
            ):
                return False
            return _modes_seeded(cursor)


def _run_sql_file(cursor, file_path: Path) -> None:
    for statement in file_path.read_text(encoding="utf-8").split(";"):
        sql = statement.strip()
        if sql:
            cursor.execute(sql)


def initialize_database() -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            _run_sql_file(cursor, SCHEMA_FILE)
            _run_sql_file(cursor, SEED_FILE)
        conn.commit()


def ensure_database_setup() -> None:
    _wait_for_database()

    if database_ready():
        return

    auto_init = _env_bool("AUTO_INIT_DB", default=False)
    if auto_init:
        initialize_database()
        return

    if not sys.stdin.isatty():
        raise RuntimeError(
            "Database is not initialized. Set AUTO_INIT_DB=true for container startup, or run from a terminal to approve setup."
        )

    answer = (
        input("Database schema or seed data is missing. Initialize it now? [y/N]: ")
        .strip()
        .lower()
    )
    if answer not in {"y", "yes"}:
        raise RuntimeError(
            "Database initialization was skipped. Create the database and run schema.sql and seed.sql."
        )

    initialize_database()
    print(
        "Database initialized from api/database/schema.sql and api/database/seed.sql."
    )
