from decimal import Decimal
from enum import Enum
import uuid
from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class OrderStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class PaymentProvider(str, Enum):
    FLUTTERWAVE = "flutterwave"
    PAYSTACK = "paystack"


class PaymentType(str, Enum):
    CARD = "card"
    CASH = "cash"
    CHARGE_TO_ROOM = "charge-to-room"


class CompanyPaymentConfig(BaseModel):
    company_id: uuid.UUID
    provider: PaymentProvider
    public_key: str
    secret_key: str
    payment_callback_url: str


class Item(BaseModel):
    item_id: uuid.UUID
    name: str
    price: Decimal


class ItemSchema(BaseModel):
    quantity: int
    item_id: int
    name: str
    price: str


class OrderReturnSchema(BaseModel):
    id: str
    guest_id: str
    company_id: str
    room_number: str
    payment_status: PaymentStatus
    order_status: OrderStatus
    items: list[ItemSchema]
