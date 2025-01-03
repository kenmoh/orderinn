from decimal import Decimal
from enum import Enum
import uuid
from pydantic import BaseModel


class Item(BaseModel):
    item_id: uuid.UUID
    name: str
    price: Decimal
    paymen_url: str


class ItemSchema(BaseModel):
    quantity: int
    items: Item


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class OrderStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
