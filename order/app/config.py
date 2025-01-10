from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    DATABASE_URL: str
    ENCRYPTION_KEY: str
    SUPER_ADMIN: str
    MANAGER: str
    CHEF: str
    WAITER: str
    GUEST: str
    HOTEL_OWNER: str
    LAUNDRY_ATTENDANT: str
    ENCRYPTION_KEY: str
    ENV: str = "production"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings():
    return Settings()
