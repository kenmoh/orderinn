from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import Session, create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from enum import Enum
from typing import Dict, Optional, Set
import uuid
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel, Session, select, delete


from ..utils.utils import Permission, Resource, UserRole


class PaymentGateway(str, Enum):
    FLUTTERWAVE = "flutterwave"
    PAYSTACK = "paystack"


class UserRolePermission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
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


class User(SQLModel, table=True):
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid1, index=True)
    email: str = Field(unique=True)
    password: str
    company_name: str | None = Field(index=True, unique=True)
    role: UserRole = Field(nullable=False)
    company_id: uuid.UUID = Field(foreign_key="user.id", index=True, nullable=True)

    is_subscribed: Optional[bool] = Field(default=False)
    subscription_start_date: Optional[datetime] = Field(default=None, nullable=True)

    role_permissions: list[RolePermission] = Relationship(
        back_populates="users",
        link_model=UserRolePermission,
        # cascade_delete=True,
        # passive_deletes=True
        # sa_relationship_kwargs={
        #     "cascade": "all, delete-orphan",
        #     'single_parent': True
        # }
    )
    profile: Optional["Profile"] = Relationship(
        back_populates="user", cascade_delete=True
    )

    company: Optional["User"] = Relationship(
        back_populates="staff",
        sa_relationship_kwargs={"remote_side": "User.id", "cascade": "all"},
    )
    staff: Optional["User"] = Relationship(
        back_populates="company", cascade_delete=True
    )
    # created_at: datetime = Field(default=datetime.now())
    created_at: datetime = Field(default_factory=datetime.now)


class Profile(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid1, primary_key=True)
    address: str | None
    cac_reg_number: str | None
    payment_gateway_key: str
    payment_gateway_secret: str
    payment_gateway: PaymentGateway
    user_id: uuid.UUID = Field(default=None, foreign_key="user.id", unique=True)
    user: Optional["User"] = Relationship(
        back_populates="profile", sa_relationship_kwargs={"uselist": False}
    )


def get_user_permissions(
    session: Session, user_role: UserRole
) -> Dict[Resource, Set[Permission]]:
    """
    Get all permissions for a specific user role.
    Returns a dictionary of resources and their allowed permissions.
    """
    role_permissions = session.exec(
        select(RolePermission).where(RolePermission.role == user_role)
    ).all()

    permissions_dict: Dict[Resource, Set[Permission]] = {}
    for rp in role_permissions:
        if rp.resource not in permissions_dict:
            permissions_dict[rp.resource] = set()
        permissions_dict[rp.resource].add(rp.permission)

    return permissions_dict


def check_user_permission(
    session: Session, user: User, resource: Resource, required_permission: Permission
) -> bool:
    """
    Check if a specific user has a specific permission for a resource.
    """
    # Query through the association table
    permission_exists = session.exec(
        select(RolePermission)
        .join(UserRolePermission)
        .where(
            UserRolePermission.user_id == user.id,
            RolePermission.resource == resource,
            RolePermission.permission == required_permission,
        )
    ).first()

    return permission_exists is not None


async def assign_role_permissions(session: Session, user: User, role: UserRole) -> None:
    """
    Assign all permissions for a role to a user.
    """
    # Get all permissions for the role
    role_permissions = session.exec(
        select(RolePermission).where(RolePermission.role == role)
    ).all()

    # Clear existing permissions
    session.exec(
        delete(UserRolePermission).where(UserRolePermission.user_id == user.id)
    )

    # Assign new permissions
    for permission in role_permissions:
        user_permission = UserRolePermission(
            user_id=user.id, role_permission_id=permission.id
        )
        session.add(user_permission)

    session.commit()


def require_permission(resource: Resource, permission: Permission):
    from app.database.database import init_db
    from ..auth.auth import get_current_user

    async def permission_checker(
        current_user: User = Depends(get_current_user),
        session: Session = Depends(init_db),
    ):
        has_permission = check_user_permission(
            session=session,
            user=current_user,
            resource=resource,
            required_permission=permission,
        )

        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail=f"You do not have {permission} permission for this {resource}",
            )

        return current_user

    return permission_checker


def deactivate_expired_subscriptions(db: Session):
    users = db.exec(select(User).where(User.is_subscribed == True)).all()
    for user in users:
        now = datetime.now()
        if user.subscription_start_date and (
            now - user.subscription_start_date
        ) > timedelta(days=30):
            user.subscription_start_date = None
            db.add(user)
            db.commit()


# async def create_user_with_permissions(
#     session: Session,
#     user_data: UserCreate
# ) -> User:
#     """
#     Create a new user and assign appropriate permissions based on their role.
#     """
#     # Create the user
#     new_user = User(
#         email=user_data.email,
#         password=get_password_hash(user_data.password),
#         company_name=user_data.full_name,
#         role=user_data.role,
#         hotel_id=user_data.hotel_id
#     )
#     session.add(new_user)
#     session.commit()

#     # Assign permissions based on role
#     await assign_role_permissions(session, new_user, user_data.role)

#     return new_user
