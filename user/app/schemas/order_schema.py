from decimal import Decimal
from typing import Any
from enum import Enum
from bson.decimal128 import Decimal128
from beanie import PydanticObjectId
from pydantic import BaseModel, Field, model_validator


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
    company_id: PydanticObjectId
    provider: PaymentProvider
    public_key: str
    secret_key: str
    payment_callback_url: str


class Item(BaseModel):
    item_id: PydanticObjectId
    company_id: PydanticObjectId
    name: str
    price: Decimal

    @model_validator(mode="before")
    @classmethod
    def convert_decimal128(cls, data: Any) -> Any:
        if isinstance(data, dict) and "price" in data:
            if isinstance(data["price"], Decimal128):
                data["price"] = data["price"].to_decimal()
        return data


class ItemSchema(BaseModel):
    quantity: int
    item: Item
    # name: str
    # price: str


class OrderReturnSchema(BaseModel):
    id: PydanticObjectId
    guest_id: PydanticObjectId
    company_id: PydanticObjectId
    room_number: str
    total_amount: Decimal
    payment_status: PaymentStatus
    order_status: OrderStatus
    items: list[ItemSchema]


class SplitTypeEnum(str, Enum):
    EVEN = 'evenly'
    PERCENTAGE = 'by-percentage'
    CUSTOM = 'custom-split'
    ITEM = 'split-by-item'


class CreateSplitSchema(BaseModel):
    amount: Decimal

    @model_validator(mode="before")
    @classmethod
    def convert_decimal128(cls, data: Any) -> Any:
        if isinstance(data, dict) and "amount" in data:
            if isinstance(data["amount"], Decimal128):
                data["amount"] = data["amount"].to_decimal()
        return data


class SplitSchema(BaseModel):
    guest_id: PydanticObjectId
    order_id: PydanticObjectId
    company_id: PydanticObjectId
    amount: Decimal
    split_type: SplitTypeEnum
    payment_url: str | None = None
    payment_status: PaymentStatus = Field(
        default_factory=PaymentStatus.PENDING)

    @model_validator(mode="before")
    @classmethod
    def convert_decimal128(cls, data: Any) -> Any:
        if isinstance(data, dict) and "total_amount" in data:
            if isinstance(data["total_amount"], Decimal128):
                data["total_amount"] = data["total_amount"].to_decimal()
        return data
