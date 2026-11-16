from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    app_name: str = "FactoryShield AI"
    environment: str = "development"

    database_url: str = Field(pattern=r"^postgresql\+asyncpg://")
    database_connect_timeout: int = Field(default=5, gt=0)

    jwt_secret_key: str = Field(min_length=32)
    jwt_expire_minutes: int = Field(default=60, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
