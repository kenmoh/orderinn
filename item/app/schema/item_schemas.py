from decimal import Decimal
from enum import Enum
import uuid
from pydantic import BaseModel

"""
Order structure
class Item(BaseModel):
    id: int
    name: str
    price: Decimal


class ItemSchema(BaseModel):
    item: Item
    quantity: int
    total_cost: Decimal


class OrderSchema(BaseModel):
    items: list[ItemSchema]
"""


class UnitType(str, Enum):
    PIECE = "piece"
    KILOGRAM = "kg"
    SHOT = "liter"


class ItemCategory(str, Enum):
    FOOD = "FOOD"
    BEVERAGE = "BEVERAGE"
    LINEN = "LINEN"


class CreateItemSchema(BaseModel):
    name: str
    description: str | None = None
    price: Decimal
    quantity: int | None = None
    unit: UnitType | None = None
    category: ItemCategory
    company_id: uuid.UUID
    reorder_point: int | None
    image_url: str | None = None


class UpdateItemSchema(BaseModel):
    name: str
    description: str
    price: Decimal
    unit: UnitType
    category: ItemCategory
    reorder_point: int
    image_url: str


class AddStockSchema(BaseModel):
    quantity: int
    notes: str | None = None
