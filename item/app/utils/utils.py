from enum import Enum
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ..config import get_settings

settings = get_settings()
security = HTTPBearer()


class UserRole(str, Enum):
    SUPER_ADMIN = settings.SUPER_ADMIN  # SaaS platform administrator
    HOTEL_OWNER = settings.HOTEL_OWNER  # Owner of a specific hotel
    MANAGER = settings.MANAGER  # Hotel manager
    CHEF = settings.CHEF  # Kitchen staff
    WAITER = settings.WAITER  # Service staff
    GUEST = settings.GUEST  # Guest user
    LAUNDRY_ATTENDANT = settings.LAUNDRY_ATTENDANT  # Laundry staff


class Resource(str, Enum):
    USER = "user"
    ITEM = "item"
    ORDER = "order"
    INVENTORY = "inventory"
    PAYMENT = "payment"
    STOCK = "stock"


class Permission(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


class ServiceError(Exception):
    """Base exception for service errors"""
    pass


class ServicePermissionError(ServiceError):
    """Raised when user doesn't have permission"""
    pass


def validate_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(credentials.credentials,
                             settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
