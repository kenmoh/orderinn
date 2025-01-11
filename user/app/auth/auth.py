from beanie import PydanticObjectId
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from user.app.models import user_model

from ..schemas.user_schema import UserReturnSchema
from ..config import get_settings
from ..database.database import get_db
from ..models.users import User


settings = get_settings()

# JWT settings
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
SECRET_KEY = settings.JWT_SECRET_KEY
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    """
    Get the current authenticated user from the JWT token.

    Args:
        token: JWT token from request
        session: Database session

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])

        id: str = payload.get("id")

        if id is None:
            raise credentials_exception

        user = await user_model.User.find(user_model.User.id == PydanticObjectId(id)).first_or_none()

        if user is None:
            raise credentials_exception

        return user

    except JWTError:
        raise credentials_exception


async def get_current_active_user(current_user=Depends(get_current_user)):
    """
    Get current user and verify they are active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)

        id: str = payload.get("id")

        if id is None:
            raise credentials_exception

        token_data = UserReturnSchema(**payload)

    except JWTError:
        raise credentials_exception
    return token_data


def token_data(request: Request):
    jwt_token = request.headers["Authorization"]
    token = jwt_token.split(" ")[1]
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied, No Valid token Provided!",
        )
    payload = jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=settings.JWT_ALGORITHM
    )

    return payload
