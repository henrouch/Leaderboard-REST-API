from fastapi import HTTPException, status

from api.db import get_connection
from api.schemas import LeaderboardEntry, ModeOut, ScoreIn
from psycopg2.extras import RealDictCursor  # type: ignore[import-untyped]
from datetime import date


MODE_ALIASES = {
    "t": "Timed",
    "timed": "Timed",
    "l": "Lives",
    "lives": "Lives",
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
    played_at = row[4].isoformat() if row[4] else None
    return LeaderboardEntry(
        username=row[0],
        hits=row[1],
        misses=row[2],
        accuracy=float(row[3]),
        played_at=played_at,
        mode=row[5],
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


def load_leaderboard(
    limit: int, offset: int, mode: str | None
) -> list[LeaderboardEntry]:
    mode_name = normalize_mode(mode) if mode else None

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                params: list[object] = []
                mode_clause = ""
                if mode_name:
                    mode_clause = "WHERE m.name = %s"
                    params.append(mode_name)

                cursor.execute(
                    f"""
                    WITH ranked_results AS (
                        SELECT
                            u.username,
                            g.hits,
                            g.misses,
                            g.accuracy,
                            g.played_at,
                            m.name AS mode,
                            ROW_NUMBER() OVER (
                                PARTITION BY u.id
                                ORDER BY g.accuracy DESC, g.hits DESC, g.misses ASC, g.played_at DESC
                            ) AS rank_in_player
                        FROM game_results g
                        JOIN users u ON g.user_id = u.id
                        JOIN game_modes m ON g.mode_id = m.id
                        {mode_clause}
                    )
                    SELECT username, hits, misses, accuracy, played_at, mode
                    FROM ranked_results
                    WHERE rank_in_player = 1
                    ORDER BY accuracy DESC, hits DESC, misses ASC, played_at DESC
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


def load_best_result(username: str) -> LeaderboardEntry:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        u.username,
                        g.hits,
                        g.misses,
                        g.accuracy,
                        g.played_at,
                        m.name AS mode
                    FROM game_results g
                    JOIN users u ON g.user_id = u.id
                    JOIN game_modes m ON g.mode_id = m.id
                    WHERE u.username = %s
                    ORDER BY g.accuracy DESC, g.hits DESC, g.misses ASC, g.played_at DESC
                    LIMIT 1
                    """,
                    (username,),
                )
                row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Player not found"
            )

        return format_entry(row)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


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
    

#RankedPlayers 
def get_ranked_players(limit: int):
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT 
                        DENSE_RANK() OVER (ORDER BY gr.hits DESC, gr.accuracy DESC) as rank,
                        u.username,
                        gr.hits,
                        gr.misses,
                        gr.accuracy,
                        gr.played_at,
                        gm.name AS mode
                    FROM game_results gr
                    JOIN users u ON gr.user_id = u.id
                    JOIN game_modes gm ON gr.mode_id = gm.id
                    ORDER BY rank
                    LIMIT %s;
                    """,
                    (limit,)
                )
                return cursor.fetchall()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

#Leaderboard
def get_filtered_leaderboard(player: str | None, mode: str | None, min_score: int | None, played_date: date | None):
    try:
        base_query = """
            SELECT 
                u.username,
                gr.hits,
                gr.misses,
                gr.accuracy,
                gr.played_at,
                gm.name AS mode
            FROM game_results gr
            JOIN users u ON gr.user_id = u.id
            JOIN game_modes gm ON gr.mode_id = gm.id
            WHERE 1=1
        """
        params = []
        
        if player:
            base_query += " AND u.username ILIKE %s" 
            params.append(f"%{player}%") 
        
        if mode:
            base_query += " AND gm.name ILIKE %s"
            params.append(f"%{mode}%")
            
        if min_score:
            base_query += " AND gr.hits >= %s"
            params.append(min_score)
            
        if played_date:
            base_query += " AND DATE(gr.played_at) = %s"
            params.append(played_date)
            
        base_query += " ORDER BY gr.hits DESC, gr.accuracy DESC"

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(base_query, tuple(params))
                return cursor.fetchall()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    


