from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    conn = psycopg2.connect(
        dbname="aimtrainer",
        user="username",
        password="",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    print("Database connected successfully")

except Exception as e:
    conn = None
    cursor = None
    print("Database not connected:", e)


class Score(BaseModel):
    username: str
    hits: int
    misses: int
    accuracy: float
    time: float
    mode: str


MODE_MAP = {"T": "Timed", "L": "Lives", "Timed": "Timed", "Lives": "Lives"}

@app.post("/scores")
def post_score(score: Score):
    if not cursor:
        return {"message": "Database not connected"}

    cursor.execute("SELECT id FROM users WHERE username = %s", (score.username,))
    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
            (score.username, "placeholder")
        )
        user_id = cursor.fetchone()[0]
    else:
        user_id = user[0]


    mode_name = MODE_MAP.get(score.mode, score.mode)
    cursor.execute("SELECT id FROM game_modes WHERE name = %s", (mode_name,))
    mode = cursor.fetchone()

    if mode is None:
        return {"message": f"Invalid game mode: '{score.mode}'. Expected T, L, Timed, or Lives."}

    mode_id = mode[0]

    cursor.execute("""
        INSERT INTO game_results (user_id, mode_id, hits, misses, accuracy)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, mode_id, score.hits, score.misses, score.accuracy))

    conn.commit()
    return {"message": "Score saved"}



