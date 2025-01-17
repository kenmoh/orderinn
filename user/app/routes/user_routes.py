import io
import os
from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse

from user.app.models import user_model

from ..auth.auth import get_current_user
from ..service.user_service import CreateRoomService, UserService, create_staff_permission_group
from ..schemas.user_schema import (
    AddStaffToOutletSchema,
    CreateGuestUserSchema,
    CreatePermissionGroupSchema,
    CreateStaffUserSchema,
    CreateUserSchema,
    GatewaySchema,
    GenerateRoomQRCodeSchema,
    GuestReturnSchema,
    NoPostRoomSchema,
    OutletSchema,
    OutletType,
    ProfileSchema,
    RolePermission,
    StaffUserReturnSchema,
    UserReturnSchema,

)
from ..models.users import User

user_router = APIRouter(tags=["Users"], prefix="/api/v1")

user_service = UserService()
room_service = CreateRoomService()


@user_router.get("/users")
async def get_users() -> list[UserReturnSchema]:
    """
    - Get a list of users.
    """
    return await user_service.get_users()


@user_router.get("/company-staff")
async def get_company_staff(current_user: user_model.User = Depends(get_current_user)) -> list[StaffUserReturnSchema]:
    """
    - Get a list of cpmpany staff.
    """
    return await user_service.get_company_staff(current_user=current_user)


@user_router.get("/users/{user_id}")
async def get_user(user_id: PydanticObjectId) -> UserReturnSchema:
    """
    - Get a single user by user ID
    """
    try:
        return await user_service.get_user(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@user_router.post("/guest-users", status_code=status.HTTP_201_CREATED)
async def create_guest_user(
    data: CreateGuestUserSchema
) -> GuestReturnSchema:
    error = await user_service.check_unique_email_staff(data.email)
    if error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error)

    return await user_service.create_guest_user(data=data)


@user_router.post("/company-users", status_code=status.HTTP_201_CREATED)
async def create_company_user(
    data: CreateUserSchema
) -> UserReturnSchema:

    try:

        return await user_service.create_company_user(data=data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))


@user_router.post("/create-staff", status_code=status.HTTP_201_CREATED)
async def create_staff_user(
    data: CreateStaffUserSchema,
    current_user: User = Depends(get_current_user),
) -> GuestReturnSchema:

    try:

        return await user_service.create_staff(
            current_user=current_user, data=data,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))


@user_router.patch("/{staff_id}/update-staff-permission", status_code=status.HTTP_202_ACCEPTED)
async def create_staff_user(
    staff_id: PydanticObjectId,
    resource_permissions: list[RolePermission],
    current_user: User = Depends(get_current_user),
) -> GuestReturnSchema:

    try:

        return await user_service.update_staff_permissions(
            current_user=current_user, resource_permissions=resource_permissions, staff_id=staff_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))


# ============== PROFILE ================
@user_router.post("/me/profile", status_code=status.HTTP_201_CREATED)
async def create_profile(
    data: ProfileSchema,
    current_user: User = Depends(get_current_user),
) -> ProfileSchema:

    try:
        return await user_service.create_profile(
            data=data, current_user=current_user
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ============== Payment Gateway ================


@user_router.post("/gateway-provider", status_code=status.HTTP_201_CREATED)
async def add_payment_gateway(
    data: GatewaySchema,
    current_user: User = Depends(get_current_user),
) -> GatewaySchema:

    try:
        return await user_service.add_payment_gateway(
            data=data, current_user=current_user
        )
    except Exception as e:
        raise HTTPException(

            status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ============== QRCoce Generation ================


@user_router.post("/{company_id}/create-qrcode", status_code=status.HTTP_201_CREATED)
async def generate_qr_code(
    company_id: PydanticObjectId,
    outlet_type: OutletType,
    numbers: GenerateRoomQRCodeSchema,
    current_user: User = Depends(get_current_user),
) -> str:
    try:
        zip_path = await room_service.generate_rooms_qrcode(
            company_id=company_id, room_no=numbers, outlet_type=outlet_type, current_user=current_user
        )
        with open(zip_path, "rb") as file:
            zip_content = io.BytesIO(file.read())
        os.remove(zip_path)

        headers = {
            "Content-Disposition": f"attachment; filename={zip_path}",
            "Content-Type": "application/zip",
        }
        return StreamingResponse(
            zip_content, headers=headers, media_type="application/zip"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============== Permissions ================


@user_router.post('/create-permission-group', status_code=status.HTTP_201_CREATED)
async def create_permission_group(data: CreatePermissionGroupSchema, current_user: User = Depends(get_current_user)) -> OutletSchema:
    return await create_staff_permission_group(data=data, current_user=current_user)


# ============== Outlet ================
@user_router.post('/create-outlet', status_code=status.HTTP_201_CREATED)
async def create_outlet(data: OutletSchema, current_user: User = Depends(get_current_user)) -> OutletSchema:

    try:
        return await user_service.create_outlet(data=data, current_user=current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))


@user_router.post('/{outlet_id}/outlet', status_code=status.HTTP_201_CREATED)
async def add_staff_to_outlet(outlet_id: PydanticObjectId, data: AddStaffToOutletSchema, current_user: User = Depends(get_current_user)):

    try:
        return await user_service.add_staff_to_outlet(outlet_id=outlet_id, staff=data, current_user=current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@user_router.get('/outlet', status_code=status.HTTP_200_OK)
async def get_company_outlet(current_user: User = Depends(get_current_user)) -> list[OutletSchema]:
    try:
        return await user_service.get_company_outlets(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============== No Post Rooms ================
@user_router.post('/add-no-post', status_code=status.HTTP_201_CREATED)
async def create_no_post_rooms(

    data: NoPostRoomSchema,
    current_user: User = Depends(get_current_user)

) -> NoPostRoomSchema:
    try:
        return await room_service.create_no_post_rooms(data=data, current_user=current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@user_router.get('/no-post-rooms', status_code=status.HTTP_200_OK)
async def gete_no_post_rooms(
    current_user: User = Depends(get_current_user)
) -> NoPostRoomSchema:

    try:
        return await room_service.get_no_post_rooms(current_user=current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
