from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.service.user_service import UserService
from app.database.database import get_session
from app.schemas.user_schema import CreateUserSchema

user_router = APIRouter(tags=["users"], prefix="/users")

user_service = UserService()


@user_router.get("")
async def get_users(session: AsyncSession = Depends(get_session)) -> list[CreateUserSchema]:
    return await user_service.get_users(session)
