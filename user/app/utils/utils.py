from enum import Enum

from ..config import get_settings

settings = get_settings()


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
