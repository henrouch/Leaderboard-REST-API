from pydantic import BaseModel, Field


class ScoreIn(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    hits: int = Field(ge=0)
    misses: int = Field(ge=0)
    accuracy: float = Field(ge=0, le=100)
    time: float = Field(ge=0)
    mode: str = Field(min_length=1, max_length=20)


class LeaderboardEntry(BaseModel):
    username: str
    hits: int
    misses: int
    accuracy: float
    played_at: str | None
    mode: str


class ModeOut(BaseModel):
    name: str
    time_limit_seconds: int | None
    lives_limit: int | None
