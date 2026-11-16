from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FactoryShield AI"
    environment: str = "development"

    database_url: str

    jwt_secret_key: str = Field(min_length=32)
    jwt_expire_minutes: int = Field(default=60, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
