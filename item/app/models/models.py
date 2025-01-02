from datetime import datetime
from decimal import Decimal
from typing import Optional, List
import uuid
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum


class StockMovementType(str, Enum):
    RECEIVED = "RECEIVED"          # New stock received
    SALES = "SALES"               # Regular sales
    ROOM_SERVICE = "ROOM_SERVICE"  # Items used for room service
    RESTAURANT = "RESTAURANT"      # Restaurant consumption
    LAUNDRY = "LAUNDRY"           # Laundry service usage
    BAR = "BAR"                   # Bar/Mini-bar consumption
    HOUSEKEEPING = "HOUSEKEEPING"  # Housekeeping supplies usage
    RETURN = "RETURN"             # Returns to inventory
    DAMAGE = "DAMAGE"             # Damaged/spoiled items
    ADJUSTMENT = "ADJUSTMENT"      # Inventory adjustments
    TRANSFER = "TRANSFER"


class Department(str, Enum):
    RESTAURANT = "RESTAURANT"
    ROOM_SERVICE = "ROOM-SERVICE"
    HOUSEKEEPING = "HOUSEKEEPING"
    LAUNDRY = "LAUNDRY"
    BAR = "BAR"
    KITCHEN = "KITCHEN"


class ItemCategory(str, Enum):
    FOOD = "FOOD"
    BEVERAGE = "BEVERAGE"
    LINEN = "LINEN"


class UnitType(str, Enum):
    PIECE = "piece"
    KILOGRAM = "kg"
    SHOT = "liter"


class ItemBase(SQLModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    unit: UnitType | None = None
    category: ItemCategory
    # quantity: int = Field(default=0)
    active: bool = Field(default=True)


class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: uuid.UUID
    reorder_point: int = Field(default=10)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    inventory: "Inventory" = Relationship(
        back_populates="item",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan", 'uselist': False}
    )


class Inventory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id", unique=True)
    quantity: int = Field(default=0)
    stock_id: Optional[int] = Field(foreign_key="stock.id")
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    item: Item = Relationship(back_populates="inventory")
    stock: list['Stock'] = Relationship(back_populates="inventory", sa_relationship_kwargs={
                                        "cascade": "all, delete-orphan"})


class Stock(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id")
    quantity: int
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    inventory: Inventory = Relationship(back_populates="stock")
