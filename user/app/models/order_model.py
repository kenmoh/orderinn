from datetime import datetime
from decimal import Decimal
from typing import Any

from beanie import Document, PydanticObjectId
from bson import Decimal128
from pydantic import Field, model_validator

from ..schemas.order_schema import (
    OrderStatus,
    ItemSchema,
    PaymentProvider,
    PaymentStatus,
    PaymentType,
    SplitSchema,
)


class Order(Document):
    guest_id: PydanticObjectId
    company_id: PydanticObjectId
    room_number: str
    total_amount: Decimal
    payment_url: str | None = None
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    order_status: OrderStatus = Field(default=OrderStatus.PENDING)
    payment_provider: PaymentProvider
    payment_type: PaymentType | None = None

    items: list[ItemSchema]
    splits: list[SplitSchema] | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "orders"

    @model_validator(mode="before")
    @classmethod
    def convert_bson_decimal128_to_decimal(cls, data: dict[str, Any]) -> Any:
        for field in data:
            if isinstance(data[field], Decimal128):
                data[field] = data[field].to_decimal()
        return data
