"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.routes import health

FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"


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

# Register API routes first so they take precedence over static file routes.
app.include_router(health.router, prefix="/api")


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
