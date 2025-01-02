from datetime import datetime
from decimal import Decimal
from typing import Optional, List
import uuid
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

from ..schema.item_schemas import ItemCategory, UnitType


class ItemBase(SQLModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    quantity: int
    unit: UnitType | None = None
    image_url: str | None = None
    category: ItemCategory


class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: uuid.UUID
    reorder_point: int | None = Field(default=10)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    inventory: "Inventory" = Relationship(
        back_populates="item",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan", "uselist": False},
    )


class Inventory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id", unique=True)
    quantity: int = Field(default=0)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    item: Item = Relationship(back_populates="inventory")
    stock: list["Stock"] = Relationship(
        back_populates="inventory",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Stock(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    inventory_id: int = Field(foreign_key="inventory.id")
    user_id: uuid.UUID
    quantity: int
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    inventory: Inventory = Relationship(back_populates="stock")
