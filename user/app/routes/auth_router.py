import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi.security.oauth2 import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel import select

from user.app.auth.auth import verify_access_token
from user.app.models import user_model

from ..utils.auth import verify_password, create_access_token
from ..models.users import RolePermission, User, UserRolePermission
from ..database.database import get_settings, get_db
from ..schemas.user_schema import LoginResponseSchema, UserReturnSchema


settings = get_settings()

login_router = APIRouter(prefix="/api/v1", tags=["Login"])
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
oath2_scheme_refresh = OAuth2PasswordBearer(tokenUrl="api/v1/refresh-token")


# @login_router.post("/login", status_code=status.HTTP_200_OK)
# async def login(
#     credentials: OAuth2PasswordRequestForm = Depends(),
#     db: AsyncSession = Depends(get_db),
# ) -> LoginResponseSchema:
#     stmt = select(User).where(User.email == credentials.username.lower())

#     user = await db.execute(stmt)
#     user = user.scalar_one_or_none()

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials!"
#         )

#     if not verify_password(credentials.password, user.password):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials!"
#         )

#     access_token = create_access_token(data={"id": str(user.id), "role": str(
#         user.role), "perm": user.role_permissions})

#     return {"access_token": access_token, "token_type": "bearer"}


@login_router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    credentials: OAuth2PasswordRequestForm = Depends(),
) -> LoginResponseSchema:
    # Find user by email
    user = await user_model.User.find_one({"email": credentials.username.lower()})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Credentials!"
        )

    if not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Credentials!"
        )

    # Extract unique resources and permissions from user's role_permissions
    resources: list[str] = []
    permissions: list[str] = []

    if user.role_permissions:
        resources = list(set(str(perm.resource)
                         for perm in user.role_permissions))
        permissions = list(set(str(perm.permission)
                           for perm in user.role_permissions))

    # Create token with user data
    token_data = {
        "id": str(user.id),
        "role": str(user.role),
        "resources": resources,
        "permissions": permissions
    }

    access_token = create_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}

# @login_router.post("/login", status_code=status.HTTP_200_OK)
# async def login(
#     credentials: OAuth2PasswordRequestForm = Depends(),
#     db: AsyncSession = Depends(get_db),
# ) -> LoginResponseSchema:
#     # Join User with UserRolePermission and RolePermission tables
#     stmt = (
#         select(User, RolePermission)
#         .join(UserRolePermission, User.id == UserRolePermission.user_id)
#         .join(RolePermission, UserRolePermission.role_permission_id == RolePermission.id)
#         .where(User.email == credentials.username.lower())
#     )

#     result = await db.execute(stmt)
#     rows = result.all()

#     if not rows:
#         # Find user without permissions to give proper error message
#         user_stmt = select(User).where(
#             User.email == credentials.username.lower())
#         user_result = await db.execute(user_stmt)
#         user = user_result.scalar_one_or_none()

#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials!"
#             )

#         # User exists but has no permissions
#         resources = []
#         permissions = []
#     else:
#         user = rows[0][0]  # First row, User object

#         # Get unique resources and permissions
#         resources = list(set(str(row[1].resource) for row in rows))
#         permissions = list(set(str(row[1].permission) for row in rows))

#     if not verify_password(credentials.password, user.password):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials!"
#         )

#     # Create token with resources as a list
#     token_data = {
#         "id": str(user.id),
#         "role": str(user.role),
#         "resources": resources,
#         "permissions": permissions
#     }

#     access_token = create_access_token(data=token_data)

#     return {"access_token": access_token, "token_type": "bearer"}


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
