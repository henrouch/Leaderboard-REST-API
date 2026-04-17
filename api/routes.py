from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, status

from api.auth import get_current_username
from api.db import ping_database
from api.schemas import (
    AuthToken,
    LeaderboardEntry,
    LoginIn,
    ModeOut,
    PlayerUpdateIn,
    RegisterIn,
    ScoreIn,
    UserOut,
)
from api.services import (
    get_user_profile,
    list_modes,
    load_best_result,
    load_date_results,
    load_leaderboard,
    load_mode_results,
    load_player_results,
    login_user,
    register_user,
    store_score,
    update_player,
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


@router.post(
    "/auth/register", response_model=AuthToken, status_code=status.HTTP_201_CREATED
)
def register(payload: RegisterIn) -> AuthToken:
    result = register_user(payload)
    return AuthToken(
        access_token=str(result["access_token"]),
        token_type=str(result["token_type"]),
        username=str(result["username"]),
    )


@router.post("/auth/login", response_model=AuthToken)
def login(payload: LoginIn) -> AuthToken:
    result = login_user(payload)
    return AuthToken(
        access_token=str(result["access_token"]),
        token_type=str(result["token_type"]),
        username=str(result["username"]),
    )


@router.get("/auth/me", response_model=UserOut)
def me(current_username: str = Depends(get_current_username)) -> UserOut:
    return get_user_profile(current_username)


@router.put("/player/{username}", response_model=UserOut)
@router.put("/Player/{username}", response_model=UserOut)
def update_player_route(
    username: str,
    payload: PlayerUpdateIn,
    current_username: str = Depends(get_current_username),
) -> UserOut:
    if current_username != username:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token does not match player.",
        )
    return update_player(username, payload)


@router.post("/scores", status_code=status.HTTP_201_CREATED)
def post_score(
    score: ScoreIn,
    current_username: str = Depends(get_current_username),
) -> dict[str, int | str]:
    if current_username != score.username:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token does not match score username.",
        )
    return store_score(score)


@router.post("/api/leaderboard", status_code=status.HTTP_201_CREATED)
def post_score_compat(score: ScoreIn) -> dict[str, int | str]:
    return store_score(score)


@router.get("/leaderboard")
def get_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    mode: str | None = Query(default=None),
    player: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    min_score: int | None = Query(default=None),
    max_score: int | None = Query(default=None),
    sort_by: str = Query(default="score"),
) -> list[LeaderboardEntry]:
    return load_leaderboard(
        limit=limit,
        offset=offset,
        mode=mode,
        player=player,
        date_from=date_from,
        date_to=date_to,
        min_score=min_score,
        max_score=max_score,
        sort_by=sort_by,
    )


@router.get("/api/leaderboard")
def get_leaderboard_compat(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    mode: str | None = Query(default=None),
    player: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    min_score: int | None = Query(default=None),
    max_score: int | None = Query(default=None),
    sort_by: str = Query(default="score"),
) -> list[LeaderboardEntry]:
    return load_leaderboard(
        limit=limit,
        offset=offset,
        mode=mode,
        player=player,
        date_from=date_from,
        date_to=date_to,
        min_score=min_score,
        max_score=max_score,
        sort_by=sort_by,
    )


@router.get("/leaderboard/score")
def get_leaderboard_by_score(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[LeaderboardEntry]:
    return load_leaderboard(limit=limit, offset=offset, sort_by="score")


@router.get("/leaderboard/player/{username}")
def get_leaderboard_by_player(
    username: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query(default="score"),
) -> list[LeaderboardEntry]:
    return load_player_results(
        username=username, limit=limit, offset=offset, sort_by=sort_by
    )


@router.get("/leaderboard/mode/{mode_name}")
def get_leaderboard_by_mode(
    mode_name: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query(default="score"),
) -> list[LeaderboardEntry]:
    return load_mode_results(
        mode=mode_name, limit=limit, offset=offset, sort_by=sort_by
    )


@router.get("/leaderboard/date")
def get_leaderboard_by_date(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    sort_by: str = Query(default="score"),
) -> list[LeaderboardEntry]:
    return load_date_results(
        limit=limit,
        offset=offset,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
    )


@router.get("/leaderboard/{username}")
def get_player_best(username: str) -> LeaderboardEntry:
    return load_best_result(username)


@router.get("/api/leaderboard/{username}")
def get_player_best_compat(username: str) -> LeaderboardEntry:
    return load_best_result(username)
