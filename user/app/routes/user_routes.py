import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from ..auth.auth import get_current_user, token_data
from ..utils.utils import UserRole
from ..service.user_service import UserService
from ..database.database import get_db
from ..schemas.user_schema import CreateUserSchema, UserReturnSchema, CreateStaffUserSchema
from ..models.users import User

user_router = APIRouter(tags=["users"], prefix="/api/v1")

user_service = UserService()


@user_router.get("/users")
async def get_users(session: AsyncSession = Depends(get_db)) -> list[UserReturnSchema]:
    return await user_service.get_users(session)


@user_router.post("/guest-users", status_code=status.HTTP_201_CREATED)
async def create_guest_user(
    data: CreateUserSchema, db: AsyncSession = Depends(get_db)
) -> UserReturnSchema:
    try:
        return await user_service.create_guest_user(user_data=data, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))


@user_router.post("/company-users", status_code=status.HTTP_201_CREATED)
async def create_company_user(
    data: CreateUserSchema, db: AsyncSession = Depends(get_db)
) -> UserReturnSchema:
    return await user_service.create_hotel_user(user_data=data, db=db)


@user_router.post("/{company_id}/staff-user", status_code=status.HTTP_201_CREATED)
async def create_staff_user(
    company_id: uuid.UUID,
    data: CreateStaffUserSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payload=Depends(token_data),
) -> UserReturnSchema:
    return await user_service.create_staff(
        company_id=company_id, current_user=current_user, user_data=data, db=db
    )
