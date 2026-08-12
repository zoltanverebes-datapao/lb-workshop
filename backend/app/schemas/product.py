"""Product Pydantic DTOs."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


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
