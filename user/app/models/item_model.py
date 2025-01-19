from datetime import datetime
from decimal import Decimal
from typing import Any

from beanie import Document, Link, PydanticObjectId
from bson import Decimal128
from pydantic import Field, model_validator

from ..schemas.item_schema import ItemCategory


class ItemStock(Document):
    item_id: PydanticObjectId
    user_id: PydanticObjectId
    company_id: PydanticObjectId
    quantity: int
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "stocks"


class Item(Document):
    name: str
    description: str
    price: Decimal
    company_id: PydanticObjectId
    user_id: PydanticObjectId
    quantity: int = 0
    unit: str  # e.g kg, piece
    reorder_point: int = 0
    category: ItemCategory
    image_url: str | None = None
    stocks: list[Link[ItemStock]] = []  # List of references to ItemStock
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "items"

    @model_validator(mode="before")
    @classmethod
    def convert_bson_decimal128_to_decimal(cls, data: dict[str, Any]) -> Any:
        for field in data:
            if isinstance(data[field], Decimal128):
                data[field] = data[field].to_decimal()
        return data
