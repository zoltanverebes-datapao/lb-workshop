"""Test-only fixture-seeding routes.

Mounted only when `APP_ENV == "test"` (see `app/main.py`), and every route
here is declared with `include_in_schema=False` so none of them reach the
OpenAPI document the frontend's type generator reads.

Each seed route first empties `stock_levels` then `products`, so fixtures are
independent of one another and of whatever a previous test left behind.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import AsyncConn, get_conn

router = APIRouter()

_MEASURES = ("pieces", "kilogram", "gram", "litre")

_TIE_IDS = [uuid.UUID(f"00000000-0000-4000-8000-{i:012d}") for i in range(1, 6)]
_TIE_NAMES = ("Tie A", "Tie B", "Tie C", "Tie D", "Tie E")


class SeedResponse(BaseModel):
    """Response body for a successful fixture seed."""

    fixture: str
    product_ids: list[str] = Field(alias="productIds")

    model_config = {"populate_by_name": True}


def _base_time() -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


async def _reset(conn: AsyncConn) -> None:
    """Empty stock_levels then products so fixtures are independent."""
    await conn.execute("DELETE FROM stock_levels")
    await conn.execute("DELETE FROM products")


async def _insert_product(
    conn: AsyncConn,
    name: str,
    created_at: datetime,
    product_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Insert a product with an explicit created_at (and optionally id)."""
    if product_id is not None:
        cursor = await conn.execute(
            """
            INSERT INTO products (id, name, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (str(product_id), name, created_at, created_at),
        )
    else:
        cursor = await conn.execute(
            """
            INSERT INTO products (name, created_at, updated_at)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (name, created_at, created_at),
        )
    row = await cursor.fetchone()
    if row is None:  # pragma: no cover -- INSERT ... RETURNING always returns a row
        raise RuntimeError("INSERT did not return a row")
    return uuid.UUID(str(row[0]))


async def _insert_stock_level(
    conn: AsyncConn,
    product_id: uuid.UUID,
    quantity: int,
    measure: str,
    created_at: datetime,
) -> None:
    await conn.execute(
        """
        INSERT INTO stock_levels (product_id, quantity, measure, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (str(product_id), quantity, measure, created_at, created_at),
    )


@router.post(
    "/seed/products/empty", response_model=SeedResponse, include_in_schema=False
)
async def seed_products_empty(conn: AsyncConn = Depends(get_conn)) -> SeedResponse:
    """Both tables emptied, nothing inserted."""
    await _reset(conn)
    return SeedResponse(fixture="empty", productIds=[])


@router.post(
    "/seed/products/three", response_model=SeedResponse, include_in_schema=False
)
async def seed_products_three(conn: AsyncConn = Depends(get_conn)) -> SeedResponse:
    """Alpha/Bravo/Charlie, one minute apart; Alpha and Charlie have stock."""
    await _reset(conn)
    base = _base_time()
    alpha = await _insert_product(conn, "Alpha", base)
    bravo = await _insert_product(conn, "Bravo", base + timedelta(minutes=1))
    charlie = await _insert_product(conn, "Charlie", base + timedelta(minutes=2))
    await _insert_stock_level(conn, alpha, 5, "pieces", base)
    await _insert_stock_level(
        conn, charlie, 12, "kilogram", base + timedelta(minutes=2)
    )
    return SeedResponse(
        fixture="three", productIds=[str(alpha), str(bravo), str(charlie)]
    )


@router.post(
    "/seed/products/twenty-five",
    response_model=SeedResponse,
    include_in_schema=False,
)
async def seed_products_twenty_five(
    conn: AsyncConn = Depends(get_conn),
) -> SeedResponse:
    """Product 01..25; Product 24 has no stock level; Product 25 has two rows."""
    await _reset(conn)
    base = _base_time()
    product_ids: list[uuid.UUID] = []
    for n in range(1, 26):
        name = f"Product {n:02d}"
        created_at = base + timedelta(minutes=n)
        product_id = await _insert_product(conn, name, created_at)
        product_ids.append(product_id)
        if n <= 23:
            measure = _MEASURES[(n - 1) % len(_MEASURES)]
            await _insert_stock_level(conn, product_id, n * 10, measure, created_at)
        elif n == 25:
            await _insert_stock_level(
                conn, product_id, 7, "gram", datetime(2026, 3, 1, tzinfo=timezone.utc)
            )
            await _insert_stock_level(
                conn,
                product_id,
                3,
                "litre",
                datetime(2026, 3, 2, tzinfo=timezone.utc),
            )
        # n == 24: no stock_levels row.
    return SeedResponse(
        fixture="twenty-five", productIds=[str(p) for p in product_ids]
    )


@router.post(
    "/seed/products/ties", response_model=SeedResponse, include_in_schema=False
)
async def seed_products_ties(conn: AsyncConn = Depends(get_conn)) -> SeedResponse:
    """5 products sharing one created_at, with fixed ids, ordered Tie A..E."""
    await _reset(conn)
    shared_created_at = datetime(2026, 2, 1, tzinfo=timezone.utc)
    product_ids: list[uuid.UUID] = []
    for tie_id, name in zip(_TIE_IDS, _TIE_NAMES, strict=True):
        product_id = await _insert_product(conn, name, shared_created_at, tie_id)
        product_ids.append(product_id)
        await _insert_stock_level(conn, product_id, 1, "pieces", shared_created_at)
    return SeedResponse(fixture="ties", productIds=[str(p) for p in product_ids])


@router.post("/seed/products/{fixture_name}", include_in_schema=False)
async def seed_products_unknown(fixture_name: str) -> None:
    """Any other fixture name -- 404, not silently accepted."""
    raise HTTPException(status_code=404, detail=f"unknown fixture: {fixture_name}")
