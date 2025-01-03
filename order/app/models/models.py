from datetime import datetime
from decimal import Decimal
import uuid
from sqlmodel import Field, SQLModel, Column, JSON

from ..schema.schemas import ItemSchema, OrderStatus, PaymentStatus


def order_id():
    return str(uuid.uuid1()).replace("-", "")


class Order(SQLModel, table=True):
    id: uuid.UUID = Field(
        primary_key=True, default_factory=order_id, index=True)
    guest_id: uuid.UUID
    company_id: uuid.UUID
    room_number: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    total_amount: Decimal
    payment_url: str | None = None
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    order_status: OrderStatus = Field(default=OrderStatus.PENDING)
    items: list[ItemSchema] = Field(sa_column=Column(JSON))
    remarks: str | None = None
