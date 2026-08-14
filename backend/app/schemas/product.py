"""Product Pydantic DTOs."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.stock_level import Measure


class ProductDTO(BaseModel):
    """Data Transfer Object for a Product."""

    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class CreateProductInput(BaseModel):
    """Input model for creating a Product."""

    name: str
    description: str | None = None


class StockLevelSummary(BaseModel):
    """The single StockLevel shown for a Product in a list view.

    See `docs/glossary.md`'s `Product.stockLevel` entry -- the row with the
    greatest `created_at`, ties broken by the greatest `id`; quantities are
    never summed across rows or measures.
    """

    quantity: int
    measure: Measure


class ProductListItem(BaseModel):
    """One row of `GET /api/products`. Exactly these three keys."""

    id: uuid.UUID
    name: str
    stock_level: StockLevelSummary | None = Field(alias="stockLevel")

    model_config = {"populate_by_name": True}


class ProductsPage(BaseModel):
    """A single keyset-paginated page of products."""

    products: list[ProductListItem]
    next_cursor: str | None = Field(alias="nextCursor")

    model_config = {"populate_by_name": True}
