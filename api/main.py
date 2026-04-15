import importlib
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.bootstrap import ensure_database_setup
from api.routes import router


app = FastAPI(title="Aim Trainer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def startup_event() -> None:
    ensure_database_setup()


if __name__ == "__main__":
    uvicorn = importlib.import_module("uvicorn")
    uvicorn.run(
        "api.main:app",
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=True,
    )
