from datetime import datetime
from decimal import Decimal
from uuid import uuid1
import pymongo
from pydantic import BaseModel, EmailStr, Field
from beanie import Document, Indexed, PydanticObjectId, Link

from ..utils.utils import UserRole, Permission, Resource
from ..schemas.user_schema import (
    GroupPermission,
    RolePermission,
    SubscriptionType,
    PaymentGatewayEnum,
    OutletType,
)


def user_id_gen() -> str:
    return str(uuid1()).replace("-", "")


class NoPostRoom(Document):
    company_id: PydanticObjectId
    no_post_list: list[str] = []

    class Settings:
        name = "no_post_list"


class Profile(BaseModel):
    """
    Profile information embedded in User document
    """

    phone_number: str
    address: str
    cac_reg_number: str
    openning_hours: str
    logo_url: str | None


class PaymentGateway(BaseModel):
    """
    Payment gateway information embedded in User document
    """

    payment_gateway_key: str
    payment_gateway_secret: str
    payment_gateway_provider: PaymentGatewayEnum


class Outlet(Document):
    name: str
    company_id: PydanticObjectId  # Reference to the company/hotel owner

    # Reference to staff members assigned to this outlet
    staff_members: list[Link["User"]] = []

    class Settings:
        name = "outlets"

        indexes = [
            "company_id",
            "name",
        ]


class QRCode(Document):
    room_or_table_numbers: str
    fill_color: str
    back_color: str
    outlet_type: OutletType
    # download_link: str | None
    company_id: PydanticObjectId
    # user_id: PydanticObjectId  # Reference to User

    class Settings:
        name = "qrcodes"
        indexes = ["company_id", "user_id"]


# Models for Permission Groups


class PermissionGroup(Document):
    """
    Defines a group of permissions that can be assigned to multiple users
    """

    name: str
    description: str | None = None
    company_id: PydanticObjectId  # Reference to the company that created this group
    permissions: list[GroupPermission] = []
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "permission_groups"
        indexes = ["company_id", "name"]


class User(Document):
    user_id: str = Field(default_factory=user_id_gen)
    email: EmailStr
    password: str
    company_name: str | None = None
    full_name: str | None = None
    # phone_number: str | None = None
    role: UserRole | None = None
    company_id: PydanticObjectId | None = None  # Reference to parent company User
    # outlet_id: PydanticObjectId | None = None  # Reference to assigned outlet

    is_subscribed: bool = False
    subscription_type: SubscriptionType | None = None
    subscription_start_date: datetime | None = None

    # Embedded documents
    role_permissions: list[RolePermission] = []
    permission_groups: list[Link[PermissionGroup]] = []
    profile: Profile | None = None
    payment_gateway: PaymentGateway | None = None

    # References
    no_post: Link[NoPostRoom] | None = None  # Link to NoPostRoom documents
    qrcodes: list[Link[QRCode]] = []  # Link to QRCode documents
    outlets: list[Link[Outlet]] = []  # Link to Outlet documents
    staff: list[Link["User"]] = []  # Link to staff User documents
    # company: Link["User"] | None = None  # Link to company User document

    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "users"
        indexes = [
            "user_id",
            "company_id",
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "hashed_password",
                "company_name": "Hotel ABC",
                "role": UserRole.HOTEL_OWNER,
            }
        }

    # Helper method to get combined permissions from individual and group assignments
    async def get_all_permissions(self) -> list[RolePermission]:
        # Start with user's individual permissions
        all_permissions = self.role_permissions.copy()

        # Add permissions from all groups
        for group_link in self.permission_groups:
            group = await group_link.fetch()
            if group:
                # Convert GroupPermission to RolePermission
                group_perms = [
                    RolePermission(resource=perm.resource, permissions=perm.permission)
                    for perm in group.permissions
                ]
                all_permissions.extend(group_perms)

        # Remove duplicates
        return list({(p.resource, p.permission) for p in all_permissions})


async def assign_role_permissions_to_owner(user: User, role: UserRole) -> None:
    """
    Assign default permissions based on user role.
    Used for initial creation of super admin, hotel owner, and guest users.
    """
    permission_mappings = {
        UserRole.SUPER_ADMIN: [
            # Super admin permissions
            (
                Resource.USER,
                [
                    Permission.CREATE,
                    Permission.READ,
                    Permission.UPDATE,
                    Permission.DELETE,
                ],
            ),
            (Resource.ORDER, [Permission.READ, Permission.UPDATE]),
            (Resource.PAYMENT, [Permission.READ]),
            (Resource.INVENTORY, [Permission.READ]),
            (Resource.STOCK, [Permission.READ]),
        ],
        UserRole.HOTEL_OWNER: [
            # Hotel owner permissions
            (
                Resource.USER,
                [
                    Permission.CREATE,
                    Permission.READ,
                    Permission.UPDATE,
                    Permission.DELETE,
                ],
            ),
            (
                Resource.ITEM,
                [
                    Permission.CREATE,
                    Permission.READ,
                    Permission.UPDATE,
                    Permission.DELETE,
                ],
            ),
            (Resource.ORDER, [Permission.READ, Permission.UPDATE]),
            (Resource.PAYMENT, [Permission.READ]),
            (
                Resource.INVENTORY,
                [
                    Permission.CREATE,
                    Permission.READ,
                    Permission.UPDATE,
                    Permission.DELETE,
                ],
            ),
            (
                Resource.STOCK,
                [
                    Permission.CREATE,
                    Permission.READ,
                    Permission.UPDATE,
                    Permission.DELETE,
                ],
            ),
        ],
        UserRole.GUEST: [
            # Guest permissions
            (
                Resource.ORDER,
                [
                    Permission.CREATE,
                    Permission.READ,
                    Permission.UPDATE,
                    Permission.DELETE,
                ],
            ),
            (Resource.PAYMENT, [Permission.READ]),
            (Resource.ITEM, [Permission.READ]),
        ],
    }

    # Get permissions for the role
    role_perms = permission_mappings.get(role, [])

    # Create RolePermission objects
    user.role_permissions = [
        RolePermission(resource=resource, permission=permissions)
        for resource, permissions in role_perms
    ]

    # Ensure the user's role is set
    user.role = role
    await user.save()
