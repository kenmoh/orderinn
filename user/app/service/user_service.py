import tempfile
from pathlib import Path
import zipfile
from beanie import Link, PydanticObjectId, WriteRules
import qrcode
from PIL import Image
from typing import List
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from cryptography.fernet import Fernet

from user.app.utils.utils import ServicePermissionError

from ..utils.auth import hash_password
from ..models import user_model
from ..models.users import RolePermission, User, UserRole, QRCode
from ..schemas.user_schema import (
    AssignGroupToStaffSchema,
    CreateGuestUserSchema,
    CreatePermissionGroupSchema,
    CreateStaffUserSchema,
    CreateUserSchema,
    GatewaySchema,
    GenerateRoomQRCodeSchema,
    GroupPermission,
    NoPostRoom,
    OutletSchema,
    ProfileSchema, OutletType, SubscriptionType, RolePermission

)
from ..utils.utils import Resource, Permission
from ..config import get_settings

settings = get_settings()

ENCRYPTION_KEY = settings.ENCRYPTION_KEY
cipher_suite = Fernet(ENCRYPTION_KEY)

# Service functions for managing groups


async def create_permission_group(
    current_user: user_model.User,
    data: CreatePermissionGroupSchema
) -> user_model.PermissionGroup:
    """Create a new permission group"""
    if current_user.role != UserRole.HOTEL_OWNER:
        raise ServicePermissionError(
            "Only hotel owners can create permission groups")

    permissions = []
    for resource, perms in data.permissions.items():
        for perm in perms:
            permissions.append(
                GroupPermission(
                    resource=Resource(resource),
                    permission=Permission(perm)
                )
            )

    group = user_model.PermissionGroup(
        name=data.name,
        description=data.description,
        company_id=current_user.id,
        permissions=permissions
    )
    await group.save()
    return group


async def get_company_permission_groups(current_user: user_model.User):
    return await user_model.PermissionGroup.find(user_model.PermissionGroup.company_id == current_user.id).to_list()


async def assign_groups_to_staff(
    current_user: User,
    staff_id: PydanticObjectId,
    data: AssignGroupToStaffSchema
) -> User:
    """Assign permission groups to a staff member"""
    # Verify the staff belongs to this company
    staff = await User.find_one({
        "_id": staff_id,
        "company_id": current_user.id
    })

    if not staff:
        raise ServicePermissionError("Staff member not found")
    # Verify all groups exist and belong to this company
    groups = await user_model.PermissionGroup.find({
        "_id": {"$in": data.group_ids},
        "company_id": current_user.id
    }).to_list()

    if len(groups) != len(data.group_ids):
        raise ServicePermissionError(
            "One or more groups not found or don't belong to your company")

    # Update staff's group assignments
    staff.permission_groups = [Link(group) for group in groups]
    await staff.save()
    return staff


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

    async def get_users(self) -> List[user_model.User]:
        return await user_model.User.find().to_list()

    async def get_user(self, user_id: PydanticObjectId) -> User:

        user = await user_model.User.find(user_model.User.id == user_id).first_or_none()

        if not user:
            raise ServicePermissionError(f'User with {user_id} not found!')

        return user

    async def check_unique_fields(
        self, email: str, company_name: str
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

        if name is not None:
            raise ServicePermissionError(
                "User with this company name already exists.")

    async def check_unique_email_staff(
        self, email: str
    ) -> bool:

        # Check email
        user = await user_model.User.find(
            user_model.User.email == email).first_or_none()
        if user:
            raise ServicePermissionError(
                "User with this email already exists.")

    # Helper function to check permissions
    def has_permission(self, user: User, resource: Resource, permission: Permission) -> bool:
        """
        Check if a user has a specific permission for a resource.
        """
        return any(
            perm.resource == resource and perm.permission == permission
            for perm in user.role_permissions
        )

    async def create_super_admin(self, data: CreateGuestUserSchema) -> User:
        user = User(
            email=data.email,
            password=hash_password(data.password),
            full_name=data.full_name,
            is_subscribed=True
        )
        await user.save()
        await user_model.assign_role_permissions_to_owner(user, UserRole.SUPER_ADMIN)
        return user

    async def create_company_user(self, data: CreateUserSchema) -> user_model.User:
        existing_user = await self.check_unique_fields(
            email=data.email, company_name=data.company_name
        )
        if existing_user:
            return existing_user

        new_user = user_model.User(
            email=data.email, company_name=data.company_name, password=hash_password(data.password))
        await new_user.save()

        await user_model.assign_role_permissions_to_owner(user=new_user, role=UserRole.HOTEL_OWNER)

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

    async def create_staff(self, current_user: user_model.User, data: CreateStaffUserSchema) -> user_model.User:
        existing_user = await self.check_unique_email_staff(email=data.email)
        if existing_user:
            return existing_user

        user = await user_model.User.find(
            user_model.User.id == current_user.id).first_or_none()

        if user is None:
            raise ServicePermissionError(
                "Invalid user.")

        if current_user.role != UserRole.HOTEL_OWNER:
            raise ServicePermissionError(
                "You are not allowed to perform this action")

        role_permissions = []

        for resource_perm in data.resource_permissions:
            for permission in resource_perm.permissions:
                role_permissions.append(
                    RolePermission(
                        resource=resource_perm.resource,
                        permission=permission
                    )
                )

        user.staff.append(user_model.User(
            company_id=current_user.id,
            full_name=data.full_name,
            email=data.email,
            role=data.role,
            role_permissions=role_permissions,
            password=hash_password(data.password),
        ))

        await user.save(link_rule=WriteRules.WRITE)

        return user.staff[-1]

    async def update_staff_permissions(
        self,
        current_user: user_model.User,
        staff_id: PydanticObjectId,
        resource_permissions: List[RolePermission]
    ) -> user_model.User:
        """Update permissions for an existing staff member"""

        # Verify the staff belongs to this company
        staff = await user_model.User.find_one({
            "_id": staff_id,
            "company_id": current_user.id
        })

        if not staff:
            raise ServicePermissionError(
                "Staff member not found or doesn't belong to your company")
        # Create new role permissions list
        new_permissions = []
        for resource_perm in resource_permissions:
            for permission in resource_perm.permissions:
                new_permissions.append(
                    RolePermission(
                        resource=resource_perm.resource,
                        permission=permission
                    )
                )

        # Update staff permissions
        staff.role_permissions = new_permissions
        await staff.save()

        return staff

    async def create_profile(
        self,
        data: ProfileSchema,
        current_user: user_model.User,
    ):
        if current_user.role != UserRole.HOTEL_OWNER:
            raise ServicePermissionError(
                "You are not allowed to perform this action")

        user = await user_model.User.find(user_model.User.id == current_user.id).first_or_none()

        if user is None:
            raise ServicePermissionError(
                "Invalid user")

        profile = user_model.Profile(
            address=data.address,
            cac_reg_number=data.cac_reg_number,
            openning_hours=data.openning_hours,
            phone_number=data.phone_number,
            logo_url=data.logo_url

        )

        user.profile = profile
        await user.save()

        return user.profile

    async def add_payment_gateway(self, data: GatewaySchema, current_user: user_model.User):
        user = await user_model.User.find(user_model.User.id == current_user.id).first_or_none()

        if not user or user.id != current_user.id:
            raise ServicePermissionError('Invalid user.')

        if current_user.role != UserRole.HOTEL_OWNER:
            raise ServicePermissionError('Permission denied.')

        gateway_provider = user_model.PaymentGateway(
            payment_gateway_key=APIGatewayCredentialsService.encrypt_value(
                data.payment_gateway_key),
            payment_gateway_secret=APIGatewayCredentialsService.encrypt_value(
                data.payment_gateway_secret),
            payment_gateway_provider=data.payment_gateway_provider

        )

        user.payment_gateway = gateway_provider
        await user.save()

        return user.payment_gateway

    async def assign_permissions_to_staff(self, staff_id: PydanticObjectId, current_user: user_model.User,  role_permissions: RolePermission):

        staff: user_model.User = user_model.User.find(
            user_model.User.id == staff_id).first_or_none()

        if not staff:
            raise ServicePermissionError('No staff with this ID exists.')

        if current_user.id != staff.company_id and current_user.role != UserRole.HOTEL_OWNER:
            raise ServicePermissionError('You can only update your own staff.')

        staff.role_permissions.append(role_permissions)
        await staff.save()

    async def create_outlet(self, data: OutletSchema, current_user: user_model.User) -> OutletSchema:

        user: user_model.User = user_model.User.find(
            user_model.User.id == current_user.id).first_or_none()
        if not user:
            raise ServicePermissionError('No user with this ID exists.')

        if current_user.role != UserRole.HOTEL_OWNER:
            raise ServicePermissionError('Invalid user.')

        outlet = user_model.Outlet(
            name=data.name, company_id=current_user.id)

        await outlet.save()

        user.outlet_id = outlet.id
        await user.save()

        return outlet

    async def get_company_outlet(current_user: user_model.User) -> list[OutletSchema]:

        outlets: user_model.Outlet = await user_model.Outlet.find(
            user_model.Outlet.company_id == current_user.company_id).to_list()

        return outlets

    async def add_staff_to_outlet(self, staff: user_model.User, current_user: user_model.User):
        staff = user_model.User.find(
            user_model.User.id == staff.id).first_or_none()
        # outlet = user_model.Outlet.find(user_model.Outlet.id == outlet_id).first_or_none()
        if not staff:
            raise ServicePermissionError('Invalid staff user.')
        if current_user.role != UserRole.HOTEL_OWNER:
            raise ServicePermissionError('Invalid user.')

        return await user_model.Outlet.add_staff_member(staff=staff)


class CreateRoomService:

    async def create_no_post_rooms(self, company_id: PydanticObjectId, current_user: user_model.User, data: NoPostRoom):
        user: user_model.User = user_model.User.find(
            user_model.User.company_id == current_user.company_id).first_or_none()

        if not user:
            raise ServicePermissionError('Invalid user.')

        if current_user.company_id == company_id:

            no_post_rooms = NoPostRoom(
                room_numbers=data.room_numbers
            )

            user.no_post = no_post_rooms

            await user.save()

            return user.no_post

    async def get_no_post_rooms(self, company_id: PydanticObjectId) -> list[NoPostRoom]:
        user: user_model.User = await user_model.User.find(
            user_model.User.company_id == company_id).first_or_none()
        if not user:
            raise ServicePermissionError('No user found.')

        no_post_rooms_str = user.no_post

        return no_post_rooms_str.split(',')

    async def generate_rooms_qrcode(
        self,
        company_id: PydanticObjectId,
        outlet_type: OutletType,
        room_no: GenerateRoomQRCodeSchema,
        current_user: user_model.User,
        base_url: str = "https://orderinn.com",
    ) -> str:
        """
        Generate QR codes for room numbers and return zip file path

        Args:
            company_id: PydanticObjectId of the company
            room_no: comma-separated strings of room numbers to generate QR codes for
            base_url: Base URL for QR code links

        Returns:
            str: Path to zip file containing QR codes
        """

        user = await user_model.User.find(user_model.User.id == current_user.id).first_or_none()

        if not user:
            raise ServicePermissionError('Invalid user.')

        if (
            current_user.role != UserRole.HOTEL_OWNER
            or current_user.role != UserRole.MANAGER
        ) and current_user.id != company_id:
            return ServicePermissionError("You are not allowed to perform this action")

        user.qrcodes.append(user_model.QRCode(
            company_id=company_id,
            room_or_table_numbers=room_no.room_numbers,
            fill_color=room_no.fill_color,
            back_color=room_no.back_color,
            outlet_type=outlet_type
        ))

        await user.save(link_rule=WriteRules.WRITE)

        temp_dir = Path("room-qrcodes")
        temp_dir.mkdir(exist_ok=True)

        zip_path = temp_dir / f"qrcodes-{company_id}.zip"

        with zipfile.ZipFile(zip_path, "w") as zip_file:
            for room in room_no.room_numbers.split(","):
                room = room.strip()
                if outlet_type == OutletType.ROOM:
                    room_url = f"""{base_url}/{company_id}
                                ?room={room}
                                &sk={user.payment_gateway.payment_gateway_secret}
                                &payment_provider={user.payment_gateway.payment_gateway_provider}"""
                elif outlet_type == OutletType.RESTAURANT:
                    room_url = f"""{base_url}/{company_id}
                                ?table={room}
                                &sk={user.payment_gateway.payment_gateway_secret}
                                &payment_provider={user.payment_gateway.payment_gateway_provider}"""

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=6,
                    border=4,
                )
                qr.add_data(room_url)
                qr.make(fit=True)

                qr_image = qr.make_image(
                    fill_color=room_no.fill_color, back_color=room_no.back_color).convert("RGB")

                # Open and resize the logo
                logo_url = user.profile.logo_url

                if logo_url and (logo_url.startswith("http://") or logo_url.startswith("https://")):
                    try:
                        # Load the logo (URL path)
                        response = requests.get(logo_url, stream=True)
                        logo = Image.open(response.raw)
                    except Exception as e:
                        raise ServicePermissionError(
                            'Unable to open logo', str(e))
                logo_size = min(qr_image.size) // 6
                logo = logo.resize((logo_size, logo_size))

                # Calculate logo position to center it
                x = (qr_image.size[0] - logo_size) // 2
                y = (qr_image.size[1] - logo_size) // 2

                # Paste the logo in the center of the QR code
                # Use mask for transparency
                qr_image.paste(logo, (x, y))

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
                    back_color=room_no.back_color,
                    fill_color=room_no.fill_color,
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


class PermissionChecker:
    """
    Utility class to handle permission checking from both individual and group permissions
    """
    @staticmethod
    async def has_permission(
        user: User,
        resource: Resource,
        permission: Permission
    ) -> bool:
        """
        Check if user has permission through either individual permissions or group permissions
        """
        # First check individual permissions
        individual_permission = any(
            perm.resource == resource and perm.permission == permission
            for perm in user.role_permissions
        )

        if individual_permission:
            return True

        # Then check group permissions
        for group_link in user.permission_groups:
            group = await group_link.fetch()
            if group:
                group_permission = any(
                    perm.resource == resource and perm.permission == permission
                    for perm in group.permissions
                )
                if group_permission:
                    return True

        return False

    @staticmethod
    async def get_all_permissions(user: User) -> list[RolePermission]:
        """
        Get all permissions from both individual and group assignments
        """
        # Start with individual permissions
        all_permissions = set((perm.resource, perm.permission)
                              for perm in user.role_permissions)

        # Add permissions from all groups
        for group_link in user.permission_groups:
            group = await group_link.fetch()
            if group:
                group_perms = set((perm.resource, perm.permission)
                                  for perm in group.permissions)
                all_permissions.update(group_perms)

        # Convert back to RolePermission objects
        return [
            RolePermission(resource=resource, permission=permission)
            for resource, permission in all_permissions
        ]
