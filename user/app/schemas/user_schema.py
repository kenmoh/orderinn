import datetime
from enum import Enum
import uuid
from beanie import PydanticObjectId
from pydantic import BaseModel, EmailStr, Field

from ..utils.utils import UserRole


class PaymentGateway(str, Enum):
    FLUTTERWAVE = "flutterwave"
    PAYSTACK = "paystack"


class LoginResponseSchema(BaseModel):
    access_token: str
    token_type: str


class CreateUserSchema(BaseModel):
    email: EmailStr
    company_name: str
    password: str


class CreateGuestUserSchema(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class UserReturnSchema(BaseModel):
    id: PydanticObjectId
    company_id: PydanticObjectId | None = None
    email: EmailStr
    company_name: str | None
    full_name: str | None
    is_subscribed: bool
    role: UserRole
    created_at: datetime.datetime


class ProfileSchema(BaseModel):
    api_key: str
    api_secret: str
    address: str
    cac_reg_number: str
    payment_gateway: PaymentGateway


class ProfileReturnSchema(BaseModel):
    address: str
    cac_reg_number: str
    # payment_gateway: PaymentGateway


class GenerateRoomQRCodeSchema(BaseModel):
    room_numbers: str = Field(
        ..., description="Comma-separated room numbers", example="101,102,103,104"
    )
    color: str = Field(
        "black",
        description="Color of the QR code(color name or hex value black or #cccfff)",
        example="black",
    )

    class Config:
        json_schema_extra = {
            "example": {"room_numbers": "101,102,103,104", "color": "black"}
        }


class OutletType(str, Enum):
    ROOM = "room"
    RESTAURANT = "restaurant"


class SubscriptionType(str, Enum):
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"
