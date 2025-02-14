from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    AWS_REGION_NAME: str
    AWS_COGNITO_APP_CLIENT_ID: str
    AWS_COGNITO_USER_POOL_ID: str
    ENCRYPTION_KEY: str
    USERNAME: str
    PASSWORD: str
    # REDIS_URL: str
    # MAIL_USERNAME: str
    # MAIL_PASSWORD: str
    # MAIL_FROM: str
    # MAIL_SERVER: str
    ENV: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings():
    return Settings()
