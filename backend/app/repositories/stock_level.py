"""StockLevelRepository: raw SQL CRUD for the stock_levels table."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import cast

import psycopg

from app.schemas.stock_level import CreateStockLevelInput, Measure, StockLevelDTO

_Row = tuple[uuid.UUID, uuid.UUID, int, str, datetime, datetime]


def _row_to_dto(row: _Row) -> StockLevelDTO:
    return StockLevelDTO(
        id=row[0],
        productId=row[1],
        quantity=row[2],
        measure=cast(Measure, row[3]),
        createdAt=row[4],
        updatedAt=row[5],
    )


class StockLevelRepository:
    """Async repository for stock_levels using raw SQL."""

    def __init__(self, conn: psycopg.AsyncConnection[psycopg.rows.TupleRow]) -> None:
        self._conn = conn

    async def create(self, data: CreateStockLevelInput) -> StockLevelDTO:
        """Insert a new stock level and return the created DTO."""
        cursor = await self._conn.execute(
            """
            INSERT INTO stock_levels (product_id, quantity, measure)
            VALUES (%s, %s, %s)
            RETURNING id, product_id, quantity, measure, created_at, updated_at
            """,
            (str(data.product_id), data.quantity, data.measure),
        )
        row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("INSERT did not return a row")
        return _row_to_dto(row)

    async def get_by_id(self, stock_level_id: uuid.UUID) -> StockLevelDTO | None:
        """Fetch a single stock level by id, or None if not found."""
        cursor = await self._conn.execute(
            """
            SELECT id, product_id, quantity, measure, created_at, updated_at
            FROM stock_levels
            WHERE id = %s
            """,
            (str(stock_level_id),),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_dto(row)

    async def list_by_product(self, product_id: uuid.UUID) -> list[StockLevelDTO]:
        """Return all stock levels for a given product, ordered by created_at."""
        cursor = await self._conn.execute(
            """
            SELECT id, product_id, quantity, measure, created_at, updated_at
            FROM stock_levels
            WHERE product_id = %s
            ORDER BY created_at
            """,
            (str(product_id),),
        )
        rows = await cursor.fetchall()
        return [_row_to_dto(r) for r in rows]

    async def update(
        self,
        stock_level_id: uuid.UUID,
        quantity: int | None = None,
        measure: Measure | None = None,
    ) -> StockLevelDTO | None:
        """Update a stock level's fields; return updated DTO or None if not found."""
        cursor = await self._conn.execute(
            """
            UPDATE stock_levels
            SET quantity   = COALESCE(%s, quantity),
                measure    = COALESCE(%s, measure),
                updated_at = now()
            WHERE id = %s
            RETURNING id, product_id, quantity, measure, created_at, updated_at
            """,
            (quantity, measure, str(stock_level_id)),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_dto(row)

    async def delete(self, stock_level_id: uuid.UUID) -> bool:
        """Delete a stock level by id. Returns True if a row was deleted."""
        result = await self._conn.execute(
            "DELETE FROM stock_levels WHERE id = %s",
            (str(stock_level_id),),
        )
        return (result.rowcount or 0) > 0
