from __future__ import annotations

import importlib
import os

from api.bootstrap import ensure_database_setup


def main() -> None:
    ensure_database_setup()
    uvicorn = importlib.import_module("uvicorn")
    uvicorn.run(
        "api.main:app",
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=True,
    )


if __name__ == "__main__":
    main()
