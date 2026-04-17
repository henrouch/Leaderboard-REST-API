from datetime import date, datetime

from fastapi import HTTPException, status
from psycopg2.extras import RealDictCursor  # type: ignore[import-untyped]

from api.auth import create_access_token, hash_password, verify_password
from api.db import get_connection
from api.schemas import (
    LeaderboardEntry,
    LoginIn,
    ModeOut,
    PlayerUpdateIn,
    RegisterIn,
    ScoreIn,
    UserOut,
)


MODE_ALIASES = {
    "t": "Timed",
    "timed": "Timed",
    "l": "Lives",
    "lives": "Lives",
}

SORT_COLUMNS = {
    "score": "score DESC",
    "accuracy": "accuracy DESC",
    "hits": "hits DESC",
    "misses": "misses ASC",
    "date": "played_at DESC",
}


def normalize_mode(mode: str) -> str:
    normalized = MODE_ALIASES.get(mode.strip().lower())
    if normalized:
        return normalized
    if mode in {"Timed", "Lives"}:
        return mode
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Invalid game mode. Use T, L, Timed, or Lives.",
    )


def normalize_sort(sort_by: str) -> str:
    key = sort_by.strip().lower()
    if key not in SORT_COLUMNS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid sort field. Use score, accuracy, hits, misses, or date.",
        )
    return SORT_COLUMNS[key]


def user_row_to_out(row) -> UserOut:
    return UserOut(id=row[0], username=row[1], created_at=row[3])


def _select_user(cursor, username: str):
    cursor.execute(
        "SELECT id, username, password_hash, created_at FROM users WHERE username = %s",
        (username,),
    )
    return cursor.fetchone()


def register_user(payload: RegisterIn) -> dict[str, object]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                row = _select_user(cursor, payload.username)
                password_hash = hash_password(payload.password)

                if row is not None:
                    if row[2] != "placeholder":
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Username already exists.",
                        )

                    cursor.execute(
                        "UPDATE users SET password_hash = %s WHERE id = %s RETURNING id, username, password_hash, created_at",
                        (password_hash, row[0]),
                    )
                    user_row = cursor.fetchone()
                else:
                    cursor.execute(
                        """
                        INSERT INTO users (username, password_hash)
                        VALUES (%s, %s)
                        RETURNING id, username, password_hash, created_at
                        """,
                        (payload.username, password_hash),
                    )
                    user_row = cursor.fetchone()

                if user_row is None:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to register user.",
                    )

                conn.commit()
                token = create_access_token(user_row[1])
                return {
                    "access_token": token,
                    "token_type": "bearer",
                    "username": user_row[1],
                    "user": user_row_to_out(user_row),
                }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


def login_user(payload: LoginIn) -> dict[str, object]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                row = _select_user(cursor, payload.username)
                if (
                    row is None
                    or row[2] == "placeholder"
                    or not verify_password(payload.password, row[2])
                ):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid username or password.",
                    )

                token = create_access_token(row[1])
                return {
                    "access_token": token,
                    "token_type": "bearer",
                    "username": row[1],
                    "user": user_row_to_out(row),
                }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


def get_user_profile(username: str) -> UserOut:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                row = _select_user(cursor, username)
                if row is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found.",
                    )
                return user_row_to_out(row)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


def update_player(username: str, payload: PlayerUpdateIn) -> UserOut:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                row = _select_user(cursor, username)
                if row is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found.",
                    )

                target_username = payload.new_username or row[1]
                if payload.new_username and payload.new_username != row[1]:
                    cursor.execute(
                        "SELECT id FROM users WHERE username = %s",
                        (payload.new_username,),
                    )
                    if cursor.fetchone() is not None:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Username already exists.",
                        )

                password_hash = row[2]
                if payload.password:
                    password_hash = hash_password(payload.password)

                cursor.execute(
                    """
                    UPDATE users
                    SET username = %s, password_hash = %s
                    WHERE id = %s
                    RETURNING id, username, password_hash, created_at
                    """,
                    (target_username, password_hash, row[0]),
                )
                updated = cursor.fetchone()
                if updated is None:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to update player.",
                    )

                conn.commit()
                return user_row_to_out(updated)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


def fetch_user_id(cursor, username: str) -> int:
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    row = cursor.fetchone()
    if row is not None:
        return row[0]

    cursor.execute(
        """
        INSERT INTO users (username, password_hash)
        VALUES (%s, %s)
        RETURNING id
        """,
        (username, "placeholder"),
    )
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user.",
        )
    return row[0]


def fetch_mode_id(cursor, mode_name: str) -> int:
    cursor.execute("SELECT id FROM game_modes WHERE name = %s", (mode_name,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game mode '{mode_name}' is not seeded in the database.",
        )
    return row[0]


def format_entry(row) -> LeaderboardEntry:
    played_at = row["played_at"].isoformat() if row["played_at"] else None
    return LeaderboardEntry(
        username=row["username"],
        hits=int(row["hits"]),
        misses=int(row["misses"]),
        accuracy=float(row["accuracy"]),
        score=int(row["score"]),
        played_at=played_at,
        mode=row["mode"],
    )


def store_score(score: ScoreIn) -> dict[str, int | str]:
    mode_name = normalize_mode(score.mode)

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                user_id = fetch_user_id(cursor, score.username)
                mode_id = fetch_mode_id(cursor, mode_name)

                cursor.execute(
                    """
                    INSERT INTO game_results (user_id, mode_id, hits, misses, accuracy)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (user_id, mode_id, score.hits, score.misses, score.accuracy),
                )
                row = cursor.fetchone()
                if row is None:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Score insert failed.",
                    )

                conn.commit()
                return {"message": "Score saved", "id": row[0]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


def _build_filter_clause(
    *,
    player: str | None = None,
    mode: str | None = None,
    date_from: datetime | date | None = None,
    date_to: datetime | date | None = None,
    min_score: int | None = None,
    max_score: int | None = None,
) -> tuple[str, list[object]]:
    clauses: list[str] = []
    params: list[object] = []

    if player:
        clauses.append("u.username ILIKE %s")
        params.append(f"%{player}%")

    if mode:
        clauses.append("m.name = %s")
        params.append(normalize_mode(mode))

    if date_from is not None:
        clauses.append("g.played_at >= %s")
        params.append(date_from)

    if date_to is not None:
        clauses.append("g.played_at <= %s")
        params.append(date_to)

    if min_score is not None:
        clauses.append("(g.hits - g.misses) >= %s")
        params.append(min_score)

    if max_score is not None:
        clauses.append("(g.hits - g.misses) <= %s")
        params.append(max_score)

    if not clauses:
        return "", params

    return "WHERE " + " AND ".join(clauses), params


def _load_results(
    *,
    limit: int,
    offset: int,
    sort_by: str = "score",
    player: str | None = None,
    mode: str | None = None,
    date_from: datetime | date | None = None,
    date_to: datetime | date | None = None,
    min_score: int | None = None,
    max_score: int | None = None,
    best_per_player: bool = True,
) -> list[LeaderboardEntry]:
    sort_clause = normalize_sort(sort_by)
    where_clause, params = _build_filter_clause(
        player=player,
        mode=mode,
        date_from=date_from,
        date_to=date_to,
        min_score=min_score,
        max_score=max_score,
    )

    cte = f"""
    WITH filtered_results AS (
        SELECT
            u.id AS user_id,
            u.username,
            g.hits,
            g.misses,
            g.accuracy,
            g.played_at,
            m.name AS mode,
            (g.hits - g.misses) AS score
        FROM game_results g
        JOIN users u ON g.user_id = u.id
        JOIN game_modes m ON g.mode_id = m.id
        {where_clause}
    ), ranked_results AS (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY user_id
                ORDER BY {sort_clause}, accuracy DESC, hits DESC, misses ASC, played_at DESC
            ) AS rank_in_player
        FROM filtered_results
    )
    """

    select_source = (
        "ranked_results WHERE rank_in_player = 1"
        if best_per_player
        else "filtered_results"
    )

    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    f"""
                    {cte}
                    SELECT username, hits, misses, accuracy, score, played_at, mode
                    FROM {select_source}
                    ORDER BY {sort_clause}, accuracy DESC, hits DESC, misses ASC, played_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    [*params, limit, offset],
                )
                return [format_entry(row) for row in cursor.fetchall()]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


def load_leaderboard(
    limit: int,
    offset: int,
    mode: str | None = None,
    player: str | None = None,
    date_from: datetime | date | None = None,
    date_to: datetime | date | None = None,
    min_score: int | None = None,
    max_score: int | None = None,
    sort_by: str = "score",
) -> list[LeaderboardEntry]:
    return _load_results(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        player=player,
        mode=mode,
        date_from=date_from,
        date_to=date_to,
        min_score=min_score,
        max_score=max_score,
        best_per_player=True,
    )


def load_player_results(
    username: str,
    limit: int,
    offset: int,
    sort_by: str = "score",
) -> list[LeaderboardEntry]:
    return _load_results(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        player=username,
        best_per_player=False,
    )


def load_mode_results(
    mode: str,
    limit: int,
    offset: int,
    sort_by: str = "score",
) -> list[LeaderboardEntry]:
    return _load_results(
        limit=limit,
        offset=offset,
        mode=mode,
        sort_by=sort_by,
        best_per_player=False,
    )


def load_date_results(
    *,
    limit: int,
    offset: int,
    date_from: datetime | date | None = None,
    date_to: datetime | date | None = None,
    sort_by: str = "score",
) -> list[LeaderboardEntry]:
    return _load_results(
        limit=limit,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        best_per_player=False,
    )


def load_best_result(username: str) -> LeaderboardEntry:
    results = load_player_results(username=username, limit=1, offset=0, sort_by="score")
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Player not found"
        )
    return results[0]


def list_modes() -> list[ModeOut]:
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT name, time_limit_seconds, lives_limit
                    FROM game_modes
                    ORDER BY id
                    """
                )
                return [ModeOut(**row) for row in cursor.fetchall()]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
