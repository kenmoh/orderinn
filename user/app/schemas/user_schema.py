import datetime
import uuid
from pydantic import BaseModel, EmailStr

from ..utils.utils import UserRole


class LoginResponseSchema(BaseModel):
    access_token: str
    token_type: str


class CreateUserSchema(BaseModel):
    email: EmailStr
    company_name: str
    password: str


class CreateStaffUserSchema(CreateUserSchema):
    role: UserRole


class UserReturnSchema(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID | None = None
    email: EmailStr
    company_name: str
    is_subscribed: bool
    role: UserRole
    created_at: datetime.datetime
