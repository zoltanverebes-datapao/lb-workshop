"""Tests for the paginated product read path: repository + indexes.

`db_conn` (from `conftest.py`) is a raw connection with autocommit off, and
the session's `pytest_runtest_teardown` hook truncates `products` and
`stock_levels` right after each test via a second connection. That hook can
run before this file's own fixture teardown closes `db_conn`, so a test that
raises (e.g. a failed assertion) before an explicit commit would leave the
transaction open and the truncate would block forever on its locks. Every
test here therefore commits in a `finally` block -- guaranteed to run during
the test's own "call" phase, before any teardown phase begins -- regardless
of whether the test body raises.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from app.repositories.product import ProductRepository
from app.schemas.product import CreateProductInput

Conn = psycopg.AsyncConnection[psycopg.rows.TupleRow]


@asynccontextmanager
async def _auto_commit(conn: Conn) -> AsyncIterator[None]:
    """Always commit on exit, pass or fail, so the connection never lingers
    "idle in transaction" into the next test's truncate."""
    try:
        yield
    finally:
        await conn.commit()


async def _make_product(conn: Conn, name: str, created_at: datetime) -> str:
    """Insert a product with an explicit created_at, return its id as str."""
    cursor = await conn.execute(
        """
        INSERT INTO products (name, created_at, updated_at)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (name, created_at, created_at),
    )
    row = await cursor.fetchone()
    assert row is not None
    return str(row[0])


async def _make_stock_level(
    conn: Conn, product_id: str, quantity: int, measure: str, created_at: datetime
) -> None:
    """Insert a stock level with an explicit created_at (bypassing `now()`, which
    is per-transaction and would tie two rows inserted in the same test)."""
    await conn.execute(
        """
        INSERT INTO stock_levels (product_id, quantity, measure, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (product_id, quantity, measure, created_at, created_at),
    )


@pytest.mark.asyncio
async def test_indexes_exist(db_conn: Conn) -> None:
    """Migration 0002's composite indexes exist with the right leading columns."""
    async with _auto_commit(db_conn):
        cursor = await db_conn.execute(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename IN ('products', 'stock_levels')
              AND indexname IN (
                  'idx_products_created_at_id',
                  'idx_stock_levels_product_id_created_at'
              )
            """
        )
        rows = await cursor.fetchall()
        by_name = {row[0]: row[1] for row in rows}

        assert "idx_products_created_at_id" in by_name
        assert "idx_stock_levels_product_id_created_at" in by_name
        assert "created_at" in by_name["idx_products_created_at_id"]
        assert "id" in by_name["idx_products_created_at_id"]
        assert "created_at" in by_name["idx_stock_levels_product_id_created_at"]


@pytest.mark.asyncio
async def test_list_page_orders_by_created_at_then_id(db_conn: Conn) -> None:
    """Products come back ordered by (created_at, id) ascending."""
    async with _auto_commit(db_conn):
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        charlie = await _make_product(db_conn, "Charlie", base + timedelta(minutes=2))
        alpha = await _make_product(db_conn, "Alpha", base)
        bravo = await _make_product(db_conn, "Bravo", base + timedelta(minutes=1))

        repo = ProductRepository(db_conn)
        rows = await repo.list_page(limit=10, cursor=None)

        ids = [str(row[0]) for row in rows]
        assert ids == [alpha, bravo, charlie]


@pytest.mark.asyncio
async def test_list_page_extra_row_signals_next_page(db_conn: Conn) -> None:
    """limit+1 rows come back when there is a next page."""
    async with _auto_commit(db_conn):
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        for i in range(5):
            await _make_product(db_conn, f"P{i}", base + timedelta(minutes=i))

        repo = ProductRepository(db_conn)
        rows = await repo.list_page(limit=3, cursor=None)

        assert len(rows) == 4  # limit + 1


@pytest.mark.asyncio
async def test_list_page_cursor_excludes_seen_rows(db_conn: Conn) -> None:
    """Paging with a cursor returns only rows strictly after it.

    `list_page` always returns up to `limit + 1` rows (trimming to `limit`
    and turning the extra row into `nextCursor` is the route's job, not the
    repository's -- see C10/C11), so each page here is sliced to `limit`
    before comparing to the expected ids.
    """
    async with _auto_commit(db_conn):
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        ids = [
            await _make_product(db_conn, f"P{i}", base + timedelta(minutes=i))
            for i in range(5)
        ]

        repo = ProductRepository(db_conn)
        first_page = await repo.list_page(limit=2, cursor=None)
        assert len(first_page) == 3  # limit + 1: there is a next page
        assert [str(r[0]) for r in first_page[:2]] == ids[:2]

        last = first_page[1]
        cursor = (last[2], last[0])
        second_page = await repo.list_page(limit=2, cursor=cursor)
        assert [str(r[0]) for r in second_page[:2]] == ids[2:4]


@pytest.mark.asyncio
async def test_stock_level_is_latest_row_not_a_sum(db_conn: Conn) -> None:
    """A product with two stock_levels rows reports the most recent one.

    The two rows are given distinct explicit `created_at` values -- both
    inserted through `StockLevelRepository.create()` in the same transaction
    would share `now()`, making "most recent" ill-defined for this test.
    """
    async with _auto_commit(db_conn):
        product_repo = ProductRepository(db_conn)

        product = await product_repo.create(CreateProductInput(name="Widget"))
        await _make_stock_level(
            db_conn,
            str(product.id),
            7,
            "gram",
            datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        await _make_stock_level(
            db_conn,
            str(product.id),
            3,
            "litre",
            datetime(2026, 3, 2, tzinfo=timezone.utc),
        )

        rows = await product_repo.list_page(limit=10, cursor=None)
        assert len(rows) == 1
        _, _, _, quantity, measure = rows[0]
        assert quantity == 3
        assert measure == "litre"


@pytest.mark.asyncio
async def test_product_without_stock_level_is_none(db_conn: Conn) -> None:
    """A product with no stock_levels row reports (None, None)."""
    async with _auto_commit(db_conn):
        product_repo = ProductRepository(db_conn)
        await product_repo.create(CreateProductInput(name="No Stock"))

        rows = await product_repo.list_page(limit=10, cursor=None)
        assert len(rows) == 1
        _, _, _, quantity, measure = rows[0]
        assert quantity is None
        assert measure is None
