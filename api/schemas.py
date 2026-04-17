from datetime import datetime

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
    score: int
    played_at: str | None
    mode: str


class ModeOut(BaseModel):
    name: str
    time_limit_seconds: int | None
    lives_limit: int | None


class RegisterIn(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime | None = None


class PlayerUpdateIn(BaseModel):
    new_username: str | None = Field(default=None, min_length=1, max_length=50)
    password: str | None = Field(default=None, min_length=6, max_length=128)
