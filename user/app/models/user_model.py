from datetime import datetime
from uuid import uuid1
import pymongo
from pydantic import BaseModel, EmailStr, Field
from beanie import Document, Indexed, PydanticObjectId, Link

from ..utils.utils import UserRole, Permission, Resource
from ..schemas.user_schema import SubscriptionType, PaymentGateway, OutletType


def user_id_gen() -> str:
    return str(uuid1()).replace("-", "")


class RolePermission(BaseModel):
    """
    Defines what permissions each role has for different resources.
    This is embedded in the User document.
    """
    role: UserRole
    resource: Resource
    permission: Permission

    class Settings:
        name = "role_permissions"


class Profile(BaseModel):
    """
    Profile information embedded in User document
    """
    address: str | None = None
    cac_reg_number: str | None = None
    payment_gateway_key: str
    payment_gateway_secret: str
    payment_gateway: PaymentGateway


class Outlet(Document):
    name: str
    company_id: PydanticObjectId  # Reference to the company/hotel owner

    # Reference to staff members assigned to this outlet
    staff_members: list[Link["User"]] = []

    class Settings:
        name = "outlets"
        indexes = [
            "company_id",
            "name"
        ]

    async def add_staff_member(self, staff: "User"):
        if staff not in self.staff_members:
            self.staff_members.append(Link(staff))
            staff.outlet_id = self.id  # Update staff's outlet reference
            await staff.save()
            await self.save()

    async def remove_staff_member(self, staff: "User"):
        if staff in self.staff_members:
            self.staff_members.remove(Link(staff))
            staff.outlet_id = None
            await staff.save()
            await self.save()

    async def get_staff_members(self) -> list["User"]:
        """Get all staff members assigned to this outlet"""
        return await User.find({"outlet_id": str(self.id)}).to_list()


class QRCode(Document):
    room_or_table_numbers: str
    color: str
    outlet_type: OutletType
    download_link: str
    company_id: PydanticObjectId
    user_id: PydanticObjectId  # Reference to User

    class Settings:
        name = "qrcodes"
        indexes = [
            "company_id",
            "user_id"
        ]


class User(Document):
    # id: PydanticObjectId = Field(default_factory=PydanticObjectId)
    user_id: str = Field(default_factory=user_id_gen)
    email: EmailStr
    password: str
    company_name: str | None = None
    full_name: str | None = None
    role: UserRole
    company_id: PydanticObjectId | None = None  # Reference to parent company User
    outlet_id: PydanticObjectId | None = None  # Reference to assigned outlet

    is_subscribed: bool = False
    subscription_type: SubscriptionType | None = None
    subscription_start_date: datetime | None = None

    # Embedded documents
    role_permissions: list[RolePermission] = []
    profile: Profile | None = None

    # References
    qrcodes: list[Link[QRCode]] = []  # Link to QRCode documents
    staff: list[Link["User"]] = []    # Link to staff User documents
    company: Link["User"] | None = None  # Link to company User document

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
                "role": UserRole.HOTEL_OWNER
            }
        }


async def assign_role_permissions_to_owner(user: User, role: UserRole) -> None:
    """
        Assign default permissions based on user role
        """
    permission_mappings = {
        UserRole.SUPER_ADMIN: [
            # Super admin permissions
            (Resource.USER, Permission.CREATE),
            (Resource.USER, Permission.READ),
            (Resource.USER, Permission.UPDATE),
            (Resource.USER, Permission.DELETE),
            (Resource.ORDER, Permission.READ),
            (Resource.ORDER, Permission.UPDATE),
            (Resource.PAYMENT, Permission.READ),
            (Resource.INVENTORY, Permission.READ),
            (Resource.STOCK, Permission.READ),
        ],
        UserRole.HOTEL_OWNER: [
            # Hotel owner permissions
            (Resource.USER, Permission.CREATE),
            (Resource.USER, Permission.READ),
            (Resource.USER, Permission.UPDATE),
            (Resource.USER, Permission.DELETE),
            (Resource.ITEM, Permission.CREATE),
            (Resource.ITEM, Permission.READ),
            (Resource.ITEM, Permission.UPDATE),
            (Resource.ITEM, Permission.DELETE),
            (Resource.ORDER, Permission.READ),
            (Resource.ORDER, Permission.UPDATE),
            (Resource.PAYMENT, Permission.READ),
            (Resource.INVENTORY, Permission.CREATE),
            (Resource.INVENTORY, Permission.READ),
            (Resource.INVENTORY, Permission.UPDATE),
            (Resource.INVENTORY, Permission.DELETE),
            (Resource.STOCK, Permission.CREATE),
            (Resource.STOCK, Permission.READ),
            (Resource.STOCK, Permission.UPDATE),
            (Resource.STOCK, Permission.DELETE),
        ],
        UserRole.GUEST: [
            # Guest permissions
            (Resource.ORDER, Permission.CREATE),
            (Resource.ORDER, Permission.READ),
            (Resource.ORDER, Permission.UPDATE),
            (Resource.ORDER, Permission.DELETE),
            (Resource.PAYMENT, Permission.READ),
        ],

    }

    # Get permissions for the role
    role_perms = permission_mappings.get(role, [])

    # Create RolePermission objects
    user.role_permissions = [
        RolePermission(
            role=role,
            resource=resource,
            permission=permission
        )
        for resource, permission in role_perms
    ]

    await user.save()
