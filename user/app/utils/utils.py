from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"  # SaaS platform administrator
    HOTEL_OWNER = "hotel_owner"  # Owner of a specific hotel
    MANAGER = "manager"  # Hotel manager
    CHEF = "chef"  # Kitchen staff
    WAITER = "waiter"  # Service staff
    GUEST = "guest"  # Guest user
    LAUNDRY_ATTENDANT = "laundry_attendant"  # Laundry staff


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
