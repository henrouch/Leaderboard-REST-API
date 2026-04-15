import os
from contextlib import contextmanager

import psycopg2  # type: ignore[import-untyped]


@contextmanager
def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        conn = psycopg2.connect(database_url)
    else:
        conn = psycopg2.connect(
            f"dbname={os.getenv('DB_NAME', 'leaderboard_db')} "
            f"user={os.getenv('DB_USER', 'username')} "
            f"password={os.getenv('DB_PASSWORD', '')} "
            f"host={os.getenv('DB_HOST', 'localhost')} "
            f"port={os.getenv('DB_PORT', '5432')}"
        )

    try:
        yield conn
    finally:
        conn.close()


def ping_database() -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
