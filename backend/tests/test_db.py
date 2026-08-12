"""Smoke test: verify that a database connection can execute SELECT 1."""

import psycopg
import pytest


@pytest.mark.asyncio
async def test_select_one(
    db_conn: psycopg.AsyncConnection[psycopg.rows.TupleRow],
) -> None:
    """Open a connection and execute SELECT 1."""
    async with db_conn.cursor() as cur:
        await cur.execute("SELECT 1")
        result = await cur.fetchone()
    assert result is not None
    assert result[0] == 1
