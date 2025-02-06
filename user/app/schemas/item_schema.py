from datetime import datetime
from decimal import Decimal
from enum import Enum
from beanie import PydanticObjectId
from pydantic import BaseModel


class ItemCategory(str, Enum):
    FOOD = "food"
    BEVERAGE = "beverage"
    LINEN = "linen"


class CreateItemSchema(BaseModel):
    name: str
    description: str
    unit: str
    reorder_point: int
    price: Decimal
    image_url: str
    category: ItemCategory


class CreateItemReturnSchema(CreateItemSchema):
    id: PydanticObjectId


class ItemStockSchema(BaseModel):
    quantity: int
    notes: str | None = None


class ItemStockReturnSchema(ItemStockSchema):
    id: PydanticObjectId
    created_at: datetime


class InventorySchecma(BaseModel):
    id: PydanticObjectId
    name: str
    quantity: int
    unit: str
    reorder_point: int
    price: Decimal
    image_url: str
    category: ItemCategory
    description: str
    stocks: list[ItemStockSchema]
