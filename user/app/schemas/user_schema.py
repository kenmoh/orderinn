import datetime
from enum import Enum
import uuid
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


class CreateStaffUserSchema(CreateUserSchema):
    role: UserRole


class UserReturnSchema(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID | None = None
    email: EmailStr
    company_name: str
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
    payment_gateway: PaymentGateway


class GenerateRoomQRCodeSchema(BaseModel):
    room_numbers: str = Field(
        ..., description="Comma-separated room numbers", example="101,102,103,104"
    )

    class Config:
        json_schema_extra = {"example": {"room_numbers": "101,102,103,104"}}
