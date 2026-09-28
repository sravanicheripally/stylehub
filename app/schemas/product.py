from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductVariantCreate(BaseModel):
    size: str = Field(min_length=1, max_length=20)
    color: str = Field(min_length=1, max_length=50)
    stock_quantity: int = Field(default=0, ge=0)


class ProductCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    price: Decimal = Field(gt=0)
    variants: list[ProductVariantCreate] = []


class ProductVariantResponse(BaseModel):
    id: int
    size: str
    color: str
    stock_quantity: int

    model_config = {
        "from_attributes": True,
    }


class ProductImageResponse(BaseModel):
    id: int
    image_url: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ProductResponse(BaseModel):
    id: int
    category_id: int
    name: str
    description: str | None
    price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    variants: list[ProductVariantResponse] = []
    images: list[ProductImageResponse] = []

    model_config = {
        "from_attributes": True,
    }

class ProductUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )

    description: str | None = None

    price: Decimal | None = Field(
        default=None,
        gt=0,
    )

    is_active: bool | None = None