"""FastAPI application entry point."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.errors import register_error_handlers
from app.routes import health, products

FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"

APP_ENV = os.environ.get("APP_ENV")

if APP_ENV == "test":
    # Guard against ever seeding test fixtures into a database that is not
    # local: refuse to start rather than serve. See specs/S8.md.
    _database_url = os.environ.get("DATABASE_URL", "")
    _host = urlparse(_database_url).hostname
    if _host not in ("localhost", "127.0.0.1"):
        raise RuntimeError(
            "APP_ENV=test requires DATABASE_URL to point at localhost or "
            f"127.0.0.1 (got host={_host!r}); refusing to start against a "
            "non-local database."
        )


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: open pool and run migrations on startup."""
    from yoyo import get_backend, read_migrations

    # db module validates DATABASE_URL/PGHOST at import time; importing here
    # avoids raising at module import time (only raises when lifespan starts).
    from app.db import get_yoyo_url, pool

    await pool.open()

    # Run Yoyo migrations (Yoyo uses synchronous connections)
    yoyo_url = get_yoyo_url()

    migrations_path = str(Path(__file__).parent.parent / "migrations")
    backend = get_backend(yoyo_url)
    migrations = read_migrations(migrations_path)
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))

    yield

    await pool.close()


app = FastAPI(lifespan=lifespan)

register_error_handlers(app)

# Register API routes first so they take precedence over static file routes.
app.include_router(health.router, prefix="/api")
app.include_router(products.router, prefix="/api")

if APP_ENV == "test":
    from app.routes import test_seed

    app.include_router(test_seed.router, prefix="/__test__")


@app.get("/app", include_in_schema=False)
async def spa_root() -> FileResponse:
    """Serve index.html for the /app root path."""
    return FileResponse(FRONTEND_DIST / "index.html")


@app.get("/app/{path:path}", include_in_schema=False)
async def spa_fallback(path: str) -> FileResponse:
    """Serve static files or index.html for any /app/* path (SPA fallback)."""
    candidate = FRONTEND_DIST / path
    if candidate.exists() and candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(FRONTEND_DIST / "index.html")
