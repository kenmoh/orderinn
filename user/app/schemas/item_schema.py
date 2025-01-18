from decimal import Decimal
from typing import Annotated
from enum import Enum
from beanie import PydanticObjectId
from pydantic import BaseModel, field_validator
from bson import Decimal128


class ItemCategory(str, Enum):
    FOOD = "food"
    BEVERAGE = "beverage"
    LINEN = "linen"


class CreateItemSchema(BaseModel):
    name: str
    description: str
    price: Decimal
    image_url: str
    category: ItemCategory


class CreateItemReturnSchema(CreateItemSchema):
    id: PydanticObjectId
