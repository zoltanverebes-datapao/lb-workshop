"""GET /api/products -- keyset-paginated product list with current stock level."""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import RequestValidationError

from app.db import AsyncConn, get_conn
from app.errors import ErrorResponse
from app.pagination import CursorError, decode_cursor, encode_cursor
from app.repositories.product import ProductRepository
from app.schemas.product import ProductListItem, ProductsPage, StockLevelSummary
from app.schemas.stock_level import Measure

router = APIRouter()


@router.get(
    "/products",
    response_model=ProductsPage,
    responses={422: {"model": ErrorResponse}},
)
async def list_products(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    cursor: Annotated[str | None, Query()] = None,
    conn: AsyncConn = Depends(get_conn),
) -> ProductsPage:
    """Return one page of products ordered by `(created_at, id)`.

    `cursor` absent or the empty string means the first page. Any other query
    parameter is ignored. See `specs/S8.md` for the full contract.
    """
    decoded_cursor = None
    if cursor:
        try:
            decoded_cursor = decode_cursor(cursor)
        except CursorError as exc:
            raise RequestValidationError(
                errors=[
                    {
                        "type": "value_error",
                        "loc": ("query", "cursor"),
                        "msg": str(exc),
                        "input": cursor,
                    }
                ]
            ) from exc

    repo = ProductRepository(conn)
    rows = await repo.list_page(limit=limit, cursor=decoded_cursor)

    has_next = len(rows) > limit
    page_rows = rows[:limit]

    items = [
        ProductListItem(
            id=row[0],
            name=row[1],
            stockLevel=(
                StockLevelSummary(quantity=row[3], measure=cast(Measure, row[4]))
                if row[3] is not None and row[4] is not None
                else None
            ),
        )
        for row in page_rows
    ]

    next_cursor = None
    if has_next and page_rows:
        last = page_rows[-1]
        next_cursor = encode_cursor(last[2], last[0])

    return ProductsPage(products=items, nextCursor=next_cursor)
