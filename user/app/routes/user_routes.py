import io
import os
import uuid
from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from user.app.models import user_model

from ..auth.auth import get_current_user, token_data
from ..utils.utils import UserRole
from ..service.user_service import CreateRoomService, UserService
from ..database.database import get_db
from ..schemas.user_schema import (
    CreateGuestUserSchema,
    CreateUserSchema,
    GenerateRoomQRCodeSchema,
    ProfileReturnSchema,
    ProfileSchema,
    UserReturnSchema,

)
from ..models.users import User

user_router = APIRouter(tags=["Users"], prefix="/api/v1")

user_service = UserService()
room_service = CreateRoomService()


# @user_router.get("/users")
# async def get_users(session: AsyncSession = Depends(get_db)) -> list[UserReturnSchema]:
#     return await user_service.get_users(session)
@user_router.get("/users")
async def get_users() -> list[UserReturnSchema]:
    """
    - Get a list of users.
    """
    return await user_service.get_users()


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
    data: CreateUserSchema, db: AsyncSession = Depends(get_db)
) -> UserReturnSchema:
    error = await user_service.check_unique_fields(data.email, data.company_name, db)
    if error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error)

    return await user_service.create_guest_user(user_data=data, db=db)


# @user_router.post("/company-users", status_code=status.HTTP_201_CREATED)
# async def create_company_user(
#     data: CreateUserSchema, db: AsyncSession = Depends(get_db)
# ) -> UserReturnSchema:
#     error = await user_service.check_unique_fields(data.email, data.company_name, db)

#     if error:
#         raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error)

#     return await user_service.create_hotel_user(user_data=data, db=db)


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
    data: CreateGuestUserSchema,
    current_user: User = Depends(get_current_user),
) -> UserReturnSchema:
    return await user_service.create_staff(
        current_user=current_user, user_data=data,
    )
# @user_router.post("/{company_id}/staff-user", status_code=status.HTTP_201_CREATED)
# async def create_staff_user(
#     company_id: uuid.UUID,
#     data: CreateStaffUserSchema,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ) -> UserReturnSchema:
#     return await user_service.create_staff(
#         company_id=company_id, current_user=current_user, user_data=data, db=db
#     )


# PROFILE
@user_router.post("/{company_id}profile", status_code=status.HTTP_201_CREATED)
async def create_profile(
    company_id: uuid.UUID,
    data: ProfileSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileReturnSchema:
    return await user_service.create_profile(
        company_id=company_id, data=data, current_user=current_user, db=db
    )


@user_router.post("/{company_id}/create-qrcode", status_code=status.HTTP_201_CREATED)
async def generate_qr_code(
    company_id: uuid.UUID,
    room_numbers: GenerateRoomQRCodeSchema,
    current_user: User = Depends(get_current_user),
):
    try:
        zip_path = room_service.generate_rooms_qrcode(
            company_id=company_id, room=room_numbers, current_user=current_user
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
