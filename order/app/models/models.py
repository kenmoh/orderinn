from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List
import uuid
from sqlmodel import Field, SQLModel, Column
from sqlalchemy.dialects.postgresql import JSON

from ..schema.schemas import (
    ItemSchema,
    OrderStatus,
    PaymentProvider,
    PaymentStatus,
    PaymentType,
)


def order_id_gen():
    return str(uuid.uuid1()).replace("-", "")


class Order(SQLModel, table=True):
    id: str = Field(
        primary_key=True, default_factory=order_id_gen, index=True, unique=True)
    guest_id: str
    company_id: str
    room_number: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    total_amount: Decimal
    payment_url: str | None = None
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    order_status: OrderStatus = Field(default=OrderStatus.PENDING)
    payment_provider: PaymentProvider
    payment_type: PaymentType
    # items: list[Dict[str, Any]] = Field(sa_column_kwargs={"type_": JSON})
    items: List[ItemSchema] = Field(
        sa_column=Column(JSON),
        default=[]
    )
    remarks: str | None = None
