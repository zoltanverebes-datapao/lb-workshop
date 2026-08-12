"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routes import health


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: open pool and run migrations on startup."""
    import os
    from pathlib import Path

    from yoyo import get_backend, read_migrations

    # db module validates DATABASE_URL at import time; importing here avoids
    # raising at module import time (only raises when lifespan actually starts).
    from app.db import pool

    await pool.open()

    # Run Yoyo migrations (Yoyo uses synchronous connections)
    database_url = os.environ["DATABASE_URL"]

    # Convert postgresql:// to postgresql+psycopg:// for Yoyo's psycopg 3 backend
    yoyo_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    migrations_path = str(Path(__file__).parent.parent / "migrations")
    backend = get_backend(yoyo_url)
    migrations = read_migrations(migrations_path)
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))

    yield

    await pool.close()


app = FastAPI(lifespan=lifespan)

app.include_router(health.router, prefix="/api")
