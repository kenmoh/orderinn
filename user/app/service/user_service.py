import tempfile
from pathlib import Path
from unittest import result
import zipfile
from beanie import PydanticObjectId
import qrcode
import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from cryptography.fernet import Fernet

from user.app.utils.utils import ServicePermissionError

from ..utils.auth import hash_password
from ..models import user_model
from ..models.users import Profile, RolePermission, User, UserRole, UserRolePermission, QRCode
from ..schemas.user_schema import (
    CreateGuestUserSchema,
    CreateUserSchema,
    GenerateRoomQRCodeSchema,
    ProfileSchema, OutletType, SubscriptionType,
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
    # async def get_users(self, db: AsyncSession) -> List[User]:
    #     stmt = select(User).order_by(User.created_at.desc())
    #     result = await db.execute(stmt)
    #     return result.scalars().all()
    async def get_users(self) -> List[User]:
        return await user_model.User.find().to_list()

    # async def get_roles(self, db: AsyncSession, role: UserRole = None):
    #     stmt = select(RolePermission).where(RolePermission.role == role)
    #     result = await db.execute(stmt)
    #     return result.scalars().all()

    async def get_user(self, user_id: PydanticObjectId) -> User:

        user = await user_model.User.find(user_model.User.id == user_id).first_or_none()

        if not user:
            raise ServicePermissionError(f'User with {user_id} not found!')

        return user
    # async def get_user(self, user_id: int, db: AsyncSession) -> User:
    #     stmt = select(User).where(User.id == user_id)
    #     result = await db.execute(stmt)
    #     return result.scalar_one_or_none()

    # async def check_unique_fields(
    #     self, email: str, company_name: str, db: AsyncSession
    # ) -> bool:
    #     # Check email
    #     email_stmt = select(User).where(User.email == email)
    #     email_result = await db.execute(email_stmt)
    #     if email_result.scalar_one_or_none():
    #         return "User with this email already exists"

    #     # Check company name
    #     name_stmt = select(User).where(User.company_name == company_name)
    #     name_result = await db.execute(name_stmt)
    #     if name_result.scalar_one_or_none():
    #         return "User with this name already exists"
    async def check_unique_fields(
        self, email: str, company_name: str | None = None
    ) -> bool:

        # Check email
        user = await user_model.User.find(
            user_model.User.email == email).first_or_none()
        if user:
            raise ServicePermissionError(
                "User with this email already exists.")

        # Check company name
        name = await user_model.User.find(
            user_model.User.company_name == company_name).first_or_none()

        if name:
            raise ServicePermissionError(
                "User with this company name already exists.")

    async def create_company_user(self, data: CreateUserSchema) -> user_model.User:
        existing_user = await self.check_unique_fields(
            email=data.email, company_name=data.company_name
        )
        if existing_user:
            return existing_user

        new_user = user_model.User(
            email=data.email, company_name=data.company_name, password=hash_password(data.password), role=UserRole.HOTEL_OWNER)
        await new_user.save()

        await user_model.assign_role_permissions_to_owner(user=new_user, role=new_user.role)

        return new_user

    async def create_guest_user(self, data: CreateGuestUserSchema):
        existing_user = await self.check_unique_fields(
            email=data.email
        )
        if existing_user:
            return existing_user

        new_user = user_model.User(
            email=data.email, full_name=data.full_name, password=hash_password(data.password))
        await new_user.save()

        await user_model.assign_role_permissions_to_owner(user=new_user, role=UserRole.GUEST)

        return new_user

    # async def create_hotel_user(
    #     self, user_data: CreateUserSchema, db: AsyncSession
    # ) -> User:
    #     existing_user = await self.check_unique_fields(
    #         email=user_data.email, company_name=user_data.company_name, db=db
    #     )

    #     if existing_user:
    #         return existing_user

    #     new_user = User(
    #         email=user_data.email,
    #         company_name=user_data.company_name,
    #         password=hash_password(user_data.password),
    #         role=UserRole.HOTEL_OWNER,
    #     )

    #     db.add(new_user)
    #     await db.commit()
    #     await db.refresh(new_user)

        # role_permissions = await self.get_roles(db, role=UserRole.HOTEL_OWNER)

        # for role_permission in role_permissions:
        #     user_role_permission = UserRolePermission(
        #         user_id=new_user.id, role_permission_id=role_permission.id
        #     )
        #     db.add(user_role_permission)

        # await db.commit()
        # await db.refresh(new_user)
        # return new_user

    # async def create_guest_user(
    #     self, user_data: CreateUserSchema, db: AsyncSession
    # ) -> User:
    #     existing_user = await self.check_unique_fields(
    #         email=user_data.email, company_name=user_data.company_name, db=db
    #     )

    #     if existing_user:
    #         return existing_user

    #     new_user = User(
    #         email=user_data.email,
    #         company_name=user_data.company_name,
    #         password=hash_password(user_data.password),
    #         role=UserRole.GUEST,
    #     )

    #     db.add(new_user)
    #     await db.commit()
    #     await db.refresh(new_user)

    #     # Assign role permissions
    #     role_permissions = await self.get_roles(db, role=UserRole.GUEST)

    #     for role_permission in role_permissions:
    #         user_role_permission = UserRolePermission(
    #             user_id=new_user.id, role_permission_id=role_permission.id
    #         )
    #         db.add(user_role_permission)

    #     await db.commit()
    #     await db.refresh(new_user)
    #     return new_user
    async def create_staff(self, current_user: user_model.User, data: CreateGuestUserSchema) -> user_model.User:
        existing_user = await self.check_unique_fields(email=data.email)
        if existing_user:
            return existing_user

        if current_user.role != UserRole.HOTEL_OWNER:
            raise ServicePermissionError(
                "You are not allowed to perform this action")

        staff = await user_model.User(
            company_id=current_user.id,
            full_name=data.full_name,
            email=data.email,
            password=hash_password(data.password)

        )

        await staff.save()

        return staff

    # async def create_staff(
    #     self,
    #     company_id: uuid.UUID,
    #     current_user: User,
    #     user_data: CreateStaffUserSchema,
    #     db: AsyncSession,
    # ) -> User:
    #     # verify hotel owner
    #     if current_user.id != company_id and current_user.role != UserRole.HOTEL_OWNER:
    #         return "You are not allowed to perform this action"

    #     # Verify valid staff role
    #     valid_staff_roles = [
    #         UserRole.MANAGER,
    #         UserRole.CHEF,
    #         UserRole.WAITER,
    #         UserRole.LAUNDRY_ATTENDANT,
    #     ]
    #     if user_data.role not in valid_staff_roles:
    #         return "Invalid staff role"

    #     new_staff = User(
    #         email=user_data.email,
    #         company_name=user_data.company_name,
    #         password=hash_password(user_data.password),
    #         role=user_data.role,
    #         company_id=company_id,
    #     )

    #     db.add(new_staff)
    #     await db.commit()
    #     await db.refresh(new_staff)

    #     # Assign role permissions
    #     role_permissions = await self.get_roles(db, role=new_staff.role)

    #     for role_permission in role_permissions:
    #         user_role_permission = UserRolePermission(
    #             user_id=new_staff.id, role_permission_id=role_permission.id
    #         )
    #         db.add(user_role_permission)

    #     await db.commit()
    #     await db.refresh(new_staff)
    #     return new_staff

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
    async def generate_rooms_qrcode(
        self,
        company_id: uuid.UUID,
        outlet_type: OutletType,
        room_no: GenerateRoomQRCodeSchema,
        current_user: User,
        db: AsyncSession,
        base_url: str = "https://orderinn.com/room",
    ) -> str:
        """
        Generate QR codes for room numbers and return zip file path

        Args:
            company_id: UUID of the company
            room_no: List(comma-separated strings) of room numbers to generate QR codes for
            base_url: Base URL for QR code links

        Returns:
            str: Path to zip file containing QR codes
        """

        if (
            current_user.role != UserRole.HOTEL_OWNER
            or current_user.role != UserRole.MANAGER
        ) and current_user.id != company_id:
            return "You are not allowed to perform this action"

        qrcodes = QRCode(
            company_id=company_id,
            room_or_table_numbers=room_no.room_numbers,
            color=room_no.color,
        )

        db.add(qrcodes)
        await db.commit()
        db.refresh(qrcodes)

        temp_dir = Path("room-qrcodes")
        temp_dir.mkdir(exist_ok=True)

        zip_path = temp_dir / f"qrcodes-{company_id}.zip"

        with zipfile.ZipFile(zip_path, "w") as zip_file:
            for room in room_no.room_numbers.split(","):
                room = room.strip()
                if outlet_type == OutletType.ROOM:
                    room_url = f"""{base_url}/{company_id}
                                ?room={room}
                                &sk={current_user.profile.payment_gateway}
                                &payment_provider={current_user.profile.payment_gateway_secret}"""
                elif outlet_type == OutletType.RESTAURANT:
                    room_url = f"""{base_url}/{company_id}
                                ?table={room}
                                &sk={current_user.profile.payment_gateway}
                                &payment_provider={current_user.profile.payment_gateway_secret}"""

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=12,
                    border=2,
                )
                qr.add_data(room_url)
                qr.make(fit=True)

                qr_image = qr.make_image(
                    fill_color=room_no.color, back_color="white")

                # Save QR code to temporary file
                temp_file = temp_dir / f"room_{room}.png"
                qr_image.save(temp_file)

                # Add to zip file
                zip_file.write(temp_file, f"room_{room}.png")

                # Clean up temporary file
                temp_file.unlink()

            return str(zip_path)


class S3Handler:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id='your_access_key',
            aws_secret_access_key='your_secret_key',
            region_name='your_region'
        )
        self.bucket_name = 'your-bucket-name'
        self.expiration = 3600  # URL expiration time in seconds (1 hour)

    async def upload_file(self, file_path: Path, s3_key: str) -> str:
        """
        Upload a file to S3 and return a pre-signed URL
        """
        try:
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key
            )

            # Generate presigned URL for download
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=self.expiration
            )
            return url
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file to S3: {str(e)}"
            )


class QRCodeService:
    def __init__(self):
        self.s3_handler = S3Handler()
        self.temp_dir = Path("temp-qrcodes")
        self.temp_dir.mkdir(exist_ok=True)

    async def generate_rooms_qrcode(
            self,
            outlet_type: OutletType,
            room_no: GenerateRoomQRCodeSchema,
            current_user: User,
            db: AsyncSession,
            base_url: str = "https://orderinn.com/room",
    ) -> str:
        """
        Generate QR codes for room numbers and upload to S3
        """
        # Permission check
        basic_plan_qr_code_limit = 5  # Number of qr code in db
        basic_plan_qr_code_gen_limit = 20  # Number of qr code to generate
        pro_plan_qr_code_limit = 20
        pro_plan_qr_code_gen_limit = 100

        stmt = select(QRCode).where(QRCode.company_id == current_user.id)
        result = await db.execute(stmt)
        qr_codes = result.scalars().all()

        if (
            not current_user or current_user.role not in [
                UserRole.HOTEL_OWNER, UserRole.MANAGER]
        ):
            raise ServicePermissionError(
                'You are not allowed to perform this action.')

        if not current_user.is_subscribed:
            raise ServicePermissionError(
                'Please subscribe to a plan to generate QR codes.')

        if current_user.is_subscribed and current_user.subscription_type == SubscriptionType.BASIC:
            if len(qr_codes) > basic_plan_qr_code_limit and len(room_no.room_numbers.split(",")) > basic_plan_qr_code_gen_limit:
                raise ServicePermissionError(
                    f"You can only generate {basic_plan_qr_code_limit} QR codes for a basic plan."
                )

        if current_user.is_subscribed and current_user.subscription_type == SubscriptionType.PRO:
            if len(qr_codes) > pro_plan_qr_code_limit and len(room_no.room_numbers.split(",")) > pro_plan_qr_code_gen_limit:
                raise ServicePermissionError(
                    f"You can only generate {pro_plan_qr_code_limit} QR codes for a pro plan."
                )

        # Generate QR codes
        try:
            # Create temporary zip file
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir = Path(temp_dir)
                # zip_filename = f"qrcodes-{company_id}.zip"
                zip_path = zip_path = temp_dir / \
                    f"qrcodes-{current_user.id}.zip"

                with zipfile.ZipFile(zip_path, "w") as zip_file:
                    for room in room_no.room_numbers.split(","):
                        room = room.strip()

                        # Generate URL based on outlet type
                        params = {
                            "sk": current_user.profile.payment_gateway,
                            "provider": current_user.profile.payment_gateway_secret
                        }

                        if outlet_type == OutletType.ROOM:
                            params["room"] = room
                        else:
                            params["table"] = room

                        room_url = f"{base_url}/{current_user.id}"
                        for key, value in params.items():
                            room_url += f"&{key}={value}"

                        # Generate QR code
                        qr = qrcode.QRCode(
                            version=1,
                            error_correction=qrcode.constants.ERROR_CORRECT_L,
                            box_size=12,
                            border=2,
                        )
                        qr.add_data(room_url)
                        qr.make(fit=True)

                        qr_image = qr.make_image(
                            fill_color=room_no.color,
                            back_color="white"
                        )

                        # Save QR code to temporary file
                        temp_file = self.temp_dir / f"room_{room}.png"
                        qr_image.save(temp_file)

                        # Add to zip file
                        zip_file.write(temp_file, f"room_{room}.png")
                        temp_file.unlink()  # Clean up individual QR code file

                # Upload to S3
                s3_key = f"qrcodes/{current_user.id}/{zip_path.name}"
                download_link = await self.s3_handler.upload_file(zip_path, s3_key)

                # Save to database
                qrcodes = QRCode(
                    company_id=current_user.id,
                    room_or_table_numbers=room_no.room_numbers,
                    color=room_no.color,
                    outlet_type=outlet_type,
                    download_link=download_link
                )

                db.add(qrcodes)
                await db.commit()
                await db.refresh(qrcodes)

                # Clean up zip file
                zip_path.unlink()

                return download_link

        except Exception as e:
            # Clean up any remaining temporary files
            for file in self.temp_dir.glob("*"):
                file.unlink()
            raise ServicePermissionError(
                f"Failed to generate QR codes: {str(e)}")
