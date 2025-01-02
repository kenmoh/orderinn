from math import e
import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..utils.auth import hash_password
from ..models.users import RolePermission, User, UserRole, UserRolePermission
from ..schemas.user_schema import CreateUserSchema, CreateStaffUserSchema


class UserService:
    async def get_users(self, db: AsyncSession) -> List[User]:
        stmt = select(User).order_by(User.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_roles(self, db: AsyncSession, role: UserRole = None):
        stmt = select(RolePermission).where(RolePermission.role == role)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_user(self, user_id: int, db: AsyncSession) -> User:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def check_unique_fields(
        self, email: str, company_name: str, db: AsyncSession
    ) -> bool:
        # Check email
        email_stmt = select(User).where(User.email == email)
        email_result = await db.execute(email_stmt)
        if email_result.scalar_one_or_none():
            return "User with this email already exists"

        # Check comapny name
        name_stmt = select(User).where(User.company_name == company_name)
        name_result = await db.execute(name_stmt)
        if name_result.scalar_one_or_none():
            return "User with this name already exists"

    async def create_hotel_user(
        self, user_data: CreateUserSchema, db: AsyncSession
    ) -> User:
        existing_user = await self.check_unique_fields(
            email=user_data.email, company_name=user_data.company_name, db=db
        )

        if existing_user:
            return existing_user

        new_user = User(
            email=user_data.email,
            company_name=user_data.company_name,
            password=hash_password(user_data.password),
            role=UserRole.HOTEL_OWNER,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        role_permissions = await self.get_roles(db, role=UserRole.HOTEL_OWNER)

        for role_permission in role_permissions:
            user_role_permission = UserRolePermission(
                user_id=new_user.id, role_permission_id=role_permission.id
            )
            db.add(user_role_permission)

        await db.commit()
        await db.refresh(new_user)
        return new_user

    async def create_guest_user(
        self, user_data: CreateUserSchema, db: AsyncSession
    ) -> User:
        existing_user = await self.check_unique_fields(
            email=user_data.email, company_name=user_data.company_name, db=db
        )

        if existing_user:
            return existing_user

        new_user = User(
            email=user_data.email,
            company_name=user_data.company_name,
            password=hash_password(user_data.password),
            role=UserRole.GUEST,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Assign role permissions
        role_permissions = await self.get_roles(db, role=UserRole.GUEST)

        for role_permission in role_permissions:
            user_role_permission = UserRolePermission(
                user_id=new_user.id, role_permission_id=role_permission.id
            )
            db.add(user_role_permission)

        await db.commit()
        await db.refresh(new_user)
        return new_user

    async def create_staff(
        self,
        company_id: uuid.UUID,
        current_user: User,
        user_data: CreateStaffUserSchema,
        db: AsyncSession,
    ) -> User:
        # verufy hotel owner
        if current_user.id != company_id and current_user.role != UserRole.HOTEL_OWNER:
            return "You are not allowed to perform this action"

        # Verify valid staff role
        valid_staff_roles = [
            UserRole.MANAGER,
            UserRole.CHEF,
            UserRole.WAITER,
            UserRole.LAUNDRY_ATTENDANT,
        ]
        if user_data.role not in valid_staff_roles:
            return "Invalid staff role"

        new_staff = User(
            email=user_data.email,
            company_name=user_data.company_name,
            password=hash_password(user_data.password),
            role=user_data.role,
            company_id=company_id,
        )

        db.add(new_staff)
        await db.commit()
        await db.refresh(new_staff)

        # Assign role permissions
        role_permissions = await self.get_roles(db, role=new_staff.role)

        for role_permission in role_permissions:
            user_role_permission = UserRolePermission(
                user_id=new_staff.id, role_permission_id=role_permission.id
            )
            db.add(user_role_permission)

        await db.commit()
        await db.refresh(new_staff)
        return new_staff

    async def delete_user(self, user_id: int, db: AsyncSession):
        user = await self.get_user(user_id, db)
        if user:
            await db.delete(user)
            await db.commit()
