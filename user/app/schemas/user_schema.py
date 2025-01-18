import datetime
from enum import Enum
from beanie import PydanticObjectId
from pydantic import BaseModel, EmailStr, Field

from ..utils.utils import UserRole, Resource, Permission


class PaymentGateway(str, Enum):
    FLUTTERWAVE = "flutterwave"
    PAYSTACK = "paystack"


class NoPostRoomSchema(BaseModel):
    company_id: PydanticObjectId | None = None
    no_post_list: list[str]


class LoginResponseSchema(BaseModel):
    access_token: str
    token_type: str


class GroupPermission(BaseModel):
    resource: Resource
    permissions: list[Permission]


class AssignGroupToStaffSchema(BaseModel):
    group_ids: list[PydanticObjectId]


class CreateUserSchema(BaseModel):
    email: EmailStr
    company_name: str
    password: str


class CreateGuestUserSchema(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class OutletSchema(BaseModel):
    id: PydanticObjectId | None = None
    name: str


class RolePermission(BaseModel):
    """
    Defines what permissions each role has for different resources.
    This is embedded in the User document.
    """

    # role: UserRole | None = None
    resource: Resource
    permission: list[Permission]

    # class Settings:
    #     name = "role_permissions"


class AddStaffToOutletSchema(BaseModel):
    staff_ids: list[PydanticObjectId]


class CreateStaffUserSchema(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    role_permissions: list[RolePermission]
    password: str


class UserReturnSchema(BaseModel):
    id: PydanticObjectId
    company_id: PydanticObjectId | None = None
    email: EmailStr
    company_name: str | None
    full_name: str | None
    # is_subscribed: bool
    role: UserRole | None = None
    created_at: datetime.datetime


class StaffUserReturnSchema(BaseModel):
    staff: list[UserReturnSchema]


class StaffMemberSchema(BaseModel):
    full_name: str
    role: str


class AddStaffToOutletReturnSchema(BaseModel):
    id: PydanticObjectId
    name: str
    staff_members: list[StaffMemberSchema]


class GuestReturnSchema(BaseModel):
    id: PydanticObjectId
    email: EmailStr
    full_name: str
    role: UserRole | None = None
    created_at: datetime.datetime


class ProfileSchema(BaseModel):
    address: str
    cac_reg_number: str
    phone_number: str
    openning_hours: str
    logo_url: str | None = None


class GatewaySchema(BaseModel):
    payment_gateway_key: str
    payment_gateway_secret: str
    payment_gateway_provider: PaymentGateway | str


class ProfileReturnSchema(BaseModel):
    address: str
    cac_reg_number: str
    # payment_gateway: PaymentGateway


class GenerateRoomQRCodeSchema(BaseModel):
    room_numbers: str

    room_numbers: str = Field(
        ..., description="Comma-separated room numbers", example="101,102,103,104"
    )
    fill_color: str = Field(
        "black",
        description="Color of the QR code(color name or hex value black or #cccfff)",
        example="black",
    )
    back_color: str = Field(
        "black",
        description="Color of the QR code(color name or hex value red or #eeefff)",
        example="black",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "room_numbers": "101,102,103,104",
                "fill_color": "black",
                "back_color": "black",
            }
        }


class OutletType(str, Enum):
    ROOM = "room"
    RESTAURANT = "restaurant"


class SubscriptionType(str, Enum):
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class CreatePermissionGroupSchema(BaseModel):
    name: str
    description: str | None = None
    permissions: list[GroupPermission]
