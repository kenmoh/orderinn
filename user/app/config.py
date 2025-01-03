from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets

from cryptography.fernet import Fernet


# print(secrets.token_urlsafe(32))

# def generate_key():
#     return Fernet.generate_key()


# print(generate_key())


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    SUPER_ADMIN: str
    MANAGER: str
    CHEF: str
    WAITER: str
    GUEST: str
    HOTEL_OWNER: str
    LAUNDRY_ATTENDANT: str
    ENCRYPTION_KEY: str
    # ENCRYPTION_KEY: str
    # REDIS_URL: str
    # MAIL_USERNAME: str
    # MAIL_PASSWORD: str
    # MAIL_FROM: str
    # MAIL_SERVER: str
    ENV: str = "production"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings():
    return Settings()
