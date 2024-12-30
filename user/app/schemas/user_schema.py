import datetime
import uuid
from pydantic import BaseModel, EmailStr

from app.utils.utils import UserRole


class CreateUserSchema(BaseModel):
    email: EmailStr
    company_name: str
    password: str


class UserReturnSchema(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    email: EmailStr
    company_name: str
    is_subscribed: bool
    role: UserRole
    created_at: datetime.datetime
