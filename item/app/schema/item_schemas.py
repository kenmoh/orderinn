import datetime
from decimal import Decimal
from enum import Enum
import uuid
from pydantic import BaseModel


class UnitType(str, Enum):
    PIECE = "piece"
    KILOGRAM = "kg"
    SHOT = "liter"


class ItemCategory(str, Enum):
    FOOD = "food"
    BEVERAGE = "beverage"
    LINEN = "linen"


class CreateItemSchema(BaseModel):
    name: str
    description: str | None = None
    price: Decimal
    quantity: int | None = None
    unit: UnitType | None = None
    category: ItemCategory
    reorder_point: int | None
    image_url: str | None = None


class UpdateItemSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    unit: UnitType | None = None
    category: ItemCategory | None = None
    reorder_point: int | None = None
    image_url: str | None = None


class InventoryReturnSchema(BaseModel):
    company_id: str
    item_id: int
    name: str
    quantity: int
    price: Decimal
    unit: UnitType
    category: ItemCategory
    updated_at: datetime.datetime


class AddStockSchema(BaseModel):
    quantity: int
    notes: str | None = None
