"""ProductRepository: raw SQL CRUD for the products table."""

from __future__ import annotations

import uuid
from datetime import datetime

import psycopg

from app.schemas.product import CreateProductInput, ProductDTO

_Row = tuple[uuid.UUID, str, str | None, datetime, datetime]


def _row_to_dto(row: _Row) -> ProductDTO:
    return ProductDTO(
        id=row[0],
        name=row[1],
        description=row[2],
        createdAt=row[3],
        updatedAt=row[4],
    )


class ProductRepository:
    """Async repository for products using raw SQL."""

    def __init__(self, conn: psycopg.AsyncConnection[psycopg.rows.TupleRow]) -> None:
        self._conn = conn

    async def create(self, data: CreateProductInput) -> ProductDTO:
        """Insert a new product and return the created DTO."""
        cursor = await self._conn.execute(
            """
            INSERT INTO products (name, description)
            VALUES (%s, %s)
            RETURNING id, name, description, created_at, updated_at
            """,
            (data.name, data.description),
        )
        row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("INSERT did not return a row")
        return _row_to_dto(row)

    async def get_by_id(self, product_id: uuid.UUID) -> ProductDTO | None:
        """Fetch a single product by id, or None if not found."""
        cursor = await self._conn.execute(
            """
            SELECT id, name, description, created_at, updated_at
            FROM products
            WHERE id = %s
            """,
            (str(product_id),),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_dto(row)

    async def list_all(self) -> list[ProductDTO]:
        """Return all products ordered by created_at."""
        cursor = await self._conn.execute(
            """
            SELECT id, name, description, created_at, updated_at
            FROM products
            ORDER BY created_at
            """
        )
        rows = await cursor.fetchall()
        return [_row_to_dto(r) for r in rows]

    async def update(
        self,
        product_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> ProductDTO | None:
        """Update a product's fields; return updated DTO or None if not found."""
        cursor = await self._conn.execute(
            """
            UPDATE products
            SET name        = COALESCE(%s, name),
                description = COALESCE(%s, description),
                updated_at  = now()
            WHERE id = %s
            RETURNING id, name, description, created_at, updated_at
            """,
            (name, description, str(product_id)),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_dto(row)

    async def delete(self, product_id: uuid.UUID) -> bool:
        """Delete a product by id. Returns True if a row was deleted."""
        result = await self._conn.execute(
            "DELETE FROM products WHERE id = %s",
            (str(product_id),),
        )
        return (result.rowcount or 0) > 0
