from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


print(secrets.token_urlsafe(64))


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
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
