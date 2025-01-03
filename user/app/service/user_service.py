from pathlib import Path
import zipfile
import qrcode
import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from cryptography.fernet import Fernet

from user.app.utils.utils import Permission

from ..utils.auth import hash_password
from ..models.users import Profile, RolePermission, User, UserRole, UserRolePermission
from ..schemas.user_schema import (
    CreateUserSchema,
    CreateStaffUserSchema,
    GenerateRoomQRCodeSchema,
    ProfileSchema,
)
from ..config import get_settings

settings = get_settings()

ENCRYPTION_KEY = settings.ENCRYPTION_KEY
cipher_suite = Fernet(ENCRYPTION_KEY)


class APIGatewayCredentialsService:
    @staticmethod
    def encrypt_value(value: str) -> str:
        """Encrypt a string value"""
        if not value:
            return None
        encrypted_value = cipher_suite.encrypt(value.encode())
        return encrypted_value.decode()

    @staticmethod
    def decrypt_value(encrypted_value: str) -> str:
        """Decrypt an encrypted string value"""
        if not encrypted_value:
            return None
        decrypted_value = cipher_suite.decrypt(encrypted_value.encode())
        return decrypted_value.decode()


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

    async def create_profile(
        self,
        company_id: uuid.UUID,
        data: ProfileSchema,
        db: AsyncSession,
        current_user: User,
    ):
        if current_user.id != company_id and current_user.role != UserRole.HOTEL_OWNER:
            return "You are not allowed to perform this action"

        try:
            user_profile = Profile(
                address=data.address,
                cac_reg_number=data.cac_reg_number,
                payment_gateway=data.payment_gateway,
                payment_gateway_key=APIGatewayCredentialsService.encrypt_value(
                    data.api_key
                ),
                payment_gateway_secret=APIGatewayCredentialsService.encrypt_value(
                    data.api_secret
                ),
                user_id=current_user.id,
            )

            db.add(user_profile)
            await db.commit()
            await db.refresh(user_profile)
            return user_profile
        except Exception as e:
            db.rollback()
            return e

    async def update_profile(
        self,
        company_id: uuid.UUID,
        data: ProfileSchema,
        db: AsyncSession,
        current_user: User,
    ):
        if current_user.id != company_id and current_user.role != UserRole.HOTEL_OWNER:
            return "You are not allowed to perform this action"

        user_profile = Profile(
            address=data.address,
            cac_reg_number=data.cac_reg_number,
            payment_gateway=data.payment_gateway,
            payment_gateway_key=APIGatewayCredentialsService.encrypt_value(
                data.api_key
            ),
            payment_gateway_secret=APIGatewayCredentialsService.encrypt_value(
                data.api_secret
            ),
            user_id=current_user.id,
        )

        db.add(user_profile)
        await db.commit()
        await db.refresh(user_profile)
        return user_profile

    async def delete_user(self, user_id: int, db: AsyncSession):
        user = await self.get_user(user_id, db)
        if user:
            await db.delete(user)
            await db.commit()


class CreateRoomService:
    def generate_rooms_qrcode(
        self,
        company_id: uuid.UUID,
        room: GenerateRoomQRCodeSchema,
        current_user: User,
        base_url: str = "https://orderinn.com/room",
    ) -> str:
        """
        Generate QR codes for room numbers and return zip file path

        Args:
            company_id: UUID of the company
            room_numbers: List(comma-separated strings) of room numbers to generate QR codes for
            base_url: Base URL for QR code links

        Returns:
            str: Path to zip file containing QR codes
        """

        if (
            current_user.role != UserRole.HOTEL_OWNER
            or current_user.role != UserRole.MANAGER
        ) and current_user.id != company_id:
            return "You are not allowed to perform this action"

        temp_dir = Path("room-qrcodes")
        temp_dir.mkdir(exist_ok=True)

        zip_path = temp_dir / f"room-qrcodes-{company_id}.zip"

        with zipfile.ZipFile(zip_path, "w") as zip_file:
            for room in room.room_numbers.split(","):
                print(room, "XXXXXXXXXXXXXXXXXXXXXXXXXXXX")
                room = room.strip()
                room_url = f"{base_url}/{company_id}?room-number={room}"

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(room_url)
                qr.make(fit=True)

                qr_image = qr.make_image(fill_color="black", back_color="white")

                # Save QR code to temporary file
                temp_file = temp_dir / f"room_{room}.png"
                qr_image.save(temp_file)

                # Add to zip file
                zip_file.write(temp_file, f"room_{room}.png")

                # Clean up temporary file
                temp_file.unlink()

            return str(zip_path)
