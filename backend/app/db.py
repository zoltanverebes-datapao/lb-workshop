"""Async PostgreSQL connection pool and FastAPI dependency."""

import os
from collections.abc import AsyncGenerator

import psycopg
from psycopg_pool import AsyncConnectionPool

_database_url = os.environ.get("DATABASE_URL")
if not _database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is required but not set. "
        "Set it to a psycopg 3 connection string, e.g. "
        "postgresql://postgres:postgres@localhost:5432/mydb"
    )

pool: AsyncConnectionPool = AsyncConnectionPool(
    conninfo=_database_url,
    open=False,
)


AsyncConn = psycopg.AsyncConnection[psycopg.rows.TupleRow]


async def get_conn() -> AsyncGenerator[AsyncConn, None]:
    """FastAPI dependency that yields an async database connection."""
    async with pool.connection() as conn:
        yield conn
