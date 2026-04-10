from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
from datetime import datetime

app = FastAPI()

try:
    conn = psycopg2.connect(
        dbname="aimtrainer",
        user="postgres",
        password="password",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
except:
    conn = None
    cursor = None
    print("Database not connected")

class Score(BaseModel):
    username: str
    hits: int
    misses: int
    accuracy: float
    time: float
    mode: str
