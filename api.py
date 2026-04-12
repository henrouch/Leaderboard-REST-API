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
