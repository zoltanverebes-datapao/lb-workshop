"""StockLevel Pydantic DTOs."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Measure = Literal["pieces", "kilogram", "gram", "litre"]


class StockLevelDTO(BaseModel):
    """Data Transfer Object for a StockLevel."""

    id: uuid.UUID
    product_id: uuid.UUID = Field(alias="productId")
    quantity: int
    measure: Measure
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class CreateStockLevelInput(BaseModel):
    """Input model for creating a StockLevel."""

    product_id: uuid.UUID = Field(alias="productId")
    quantity: int
    measure: Measure

    model_config = {"populate_by_name": True}
