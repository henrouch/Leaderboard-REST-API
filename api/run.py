from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

import importlib
import os

from api.bootstrap import ensure_database_setup


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> None:
    ensure_database_setup()
    uvicorn = importlib.import_module("uvicorn")
    uvicorn.run(
        "api.main:app",
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=_env_bool("APP_RELOAD", default=False),
    )


if __name__ == "__main__":
    main()
