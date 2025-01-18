from datetime import datetime
from decimal import Decimal
from typing import Optional, List
import uuid
from sqlmodel import SQLModel, Field, Relationship

from beanie import Document, Link, PydanticObjectId

from ..schema.item_schemas import ItemCategory, UnitType


class ItemStock(Document):
    user_id: PydanticObjectId
    quantity: int
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = 'stocks'


class Item(Document):
    name: str
    description: Optional[str] = None
    price: Decimal
    company_id: str
    quantity: int | None = None
    unit: Optional[str] = None  # e.g kg, piece
    reorder_point: int | None = None
    category: ItemCategory
    image_url: Optional[str] = None
    stocks: list[Link[ItemStock]] = []  # List of references to ItemStock
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = 'items'


class ItemBase(SQLModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    # quantity: int
    unit: UnitType | None = None
    image_url: str | None = None
    category: ItemCategory


class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: str
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
    reorder_point: int | None = Field(default=10)
    created_at: datetime = Field(default_factory=datetime.now)
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
