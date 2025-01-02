import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi.security.oauth2 import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel import select

from user.app.auth.auth import verify_access_token

from ..utils.auth import verify_password, create_access_token
from ..models.users import User
from ..database.database import get_settings, get_db
from ..schemas.user_schema import LoginResponseSchema, UserReturnSchema


settings = get_settings()

login_router = APIRouter(prefix="/api/v1", tags=["Login"])
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
oath2_scheme_refresh = OAuth2PasswordBearer(tokenUrl="api/v1/refresh-token")


@login_router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    credentials: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> LoginResponseSchema:
    stmt = select(User).where(User.email == credentials.username.lower())

    user = await db.execute(stmt)
    user = user.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials!"
        )

    if not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials!"
        )

    access_token = create_access_token(data={"id": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}


@login_router.post("/refresh-token")
async def refresh_access_token(
    refresh_token: str = Depends(oath2_scheme_refresh),
    db: AsyncSession = Depends(get_db),
) -> UserReturnSchema:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_access_token(refresh_token, credentials_exception)
    stmt = select(User).where(User.id == token_data.id)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()

    # Create a new access token
    access_token = create_access_token(data={"id": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
