
from typing import Optional
import uuid
from datetime import datetime
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from ..schemas.user_schema import PaymentGateway, OutletType, SubscriptionType
from ..utils.utils import Permission, Resource, UserRole


class UserRolePermission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", ondelete="CASCADE")
    role_permission_id: int = Field(foreign_key="rolepermission.id")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "role_permission_id", name="unique_user_role_permission"
        ),
    )


class RolePermission(SQLModel, table=True):
    __tablename__ = "rolepermission"
    """
    Defines what permissions each role has for different resources.
    This is a separate table in the database.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    role: UserRole
    resource: Resource
    permission: Permission

    users: list["User"] = Relationship(
        back_populates="role_permissions",
        link_model=UserRolePermission,
    )

    __table_args__ = (
        UniqueConstraint(
            "role", "resource", "permission", name="unique_role_resource_permission"
        ),
    )


def user_id_gen():
    return str(uuid.uuid1()).replace("-", "")


class User(SQLModel, table=True):
    id: str = Field(
        primary_key=True, default_factory=user_id_gen, index=True, unique=True)
    email: str = Field(unique=True)
    password: str
    company_name: str | None = Field(index=True, unique=True)
    role: UserRole = Field(nullable=False)
    company_id: str = Field(foreign_key="user.id", index=True, nullable=True)

    is_subscribed: Optional[bool] = Field(default=False)
    subscription_type: SubscriptionType = Field(nullable=True)
    subscription_start_date: Optional[datetime] = Field(
        default=None, nullable=True)

    role_permissions: list[RolePermission] = Relationship(
        back_populates="users",
        link_model=UserRolePermission,
    )
    profile: Optional["Profile"] = Relationship(
        back_populates="user", cascade_delete=True
    )

    qrcodes: list['QRCode'] = Relationship(
        back_populates="user", cascade_delete=True)

    company: Optional["User"] = Relationship(
        back_populates="staff",
        sa_relationship_kwargs={"remote_side": "User.id", "cascade": "all"},
    )
    staff: Optional["User"] = Relationship(
        back_populates="company", cascade_delete=True
    )

    created_at: datetime = Field(default_factory=datetime.now)


class Profile(SQLModel, table=True):
    id: str = Field(default_factory=user_id_gen, primary_key=True, unique=True)
    address: str | None
    cac_reg_number: str | None
    payment_gateway_key: str
    payment_gateway_secret: str
    payment_gateway: PaymentGateway
    user_id: str = Field(default=None, foreign_key="user.id", unique=True)
    user: Optional["User"] = Relationship(
        back_populates="profile", sa_relationship_kwargs={"uselist": False}
    )


class QRCode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room_or_table_numbers: str
    color: str
    outlet_type: OutletType
    download_link: str
    company_id: str = Field(foreign_key="user.id", unique=True, nullable=False)
    user: Optional["User"] = Relationship(
        back_populates="qrcodes"
    )
