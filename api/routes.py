from datetime import date
from fastapi import APIRouter, Query, status

from api.db import ping_database
from api.schemas import LeaderboardEntry, ModeOut, ScoreIn
from api.services import (
    get_filtered_leaderboard,
    get_ranked_players,
    list_modes,
    load_best_result,
    load_leaderboard,
    store_score,
)

router = APIRouter()

@router.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "Aim Trainer API"}

@router.get("/health")
def health() -> dict[str, str]:
    ping_database()
    return {"status": "ok", "database": "connected"}

@router.get("/modes", response_model=list[ModeOut])
def read_modes() -> list[ModeOut]:
    return list_modes()

@router.post("/scores", status_code=status.HTTP_201_CREATED)
def post_score(score: ScoreIn) -> dict[str, int | str]:
    return store_score(score)

@router.post("/api/leaderboard", status_code=status.HTTP_201_CREATED)
def post_score_compat(score: ScoreIn) -> dict[str, int | str]:
    return store_score(score)

@router.get("/leaderboard")
def get_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    mode: str | None = Query(default=None),
) -> list[LeaderboardEntry]:
    return load_leaderboard(limit=limit, offset=offset, mode=mode)

@router.get("/api/leaderboard")
def get_leaderboard_compat(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    mode: str | None = Query(default=None),
) -> list[LeaderboardEntry]:
    return load_leaderboard(limit=limit, offset=offset, mode=mode)

@router.get("/leaderboard/top")
def get_top_players(limit: int = 10):
    return get_ranked_players(limit)

@router.get("/leaderboard/filter")
def filter_leaderboard(
    player: str | None = None,
    mode: str | None = None,
    min_score: int | None = None,
    played_date: date | None = None
):
    return get_filtered_leaderboard(player, mode, min_score, played_date)

@router.get("/leaderboard/{username}")
def get_player_best(username: str) -> LeaderboardEntry:
    return load_best_result(username)

@router.get("/api/leaderboard/{username}")
def get_player_best_compat(username: str) -> LeaderboardEntry:
    return load_best_result(username)