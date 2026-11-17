from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    app_name: str = "FactoryShield AI"
    environment: str = "development"

    database_url: str = Field(pattern=r"^postgresql\+asyncpg://")
    database_connect_timeout: int = Field(default=5, gt=0)

    jwt_secret_key: str = Field(min_length=32)
    jwt_expire_minutes: int = Field(default=60, gt=0)

    # Optional: without an API key the app still runs and only the AI assistant returns 503.
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_api_key: SecretStr | None = None
    llm_model: str = "nvidia/nemotron-3.5-super-vl:free"
    llm_timeout_seconds: float = Field(default=30, gt=0)
    llm_max_retries: int = Field(default=1, ge=0, le=5)
    llm_system_prompt: str | None = None

    # Any OpenAI-compatible /v1/embeddings service; the docker compose `embeddings` service by default.
    embedding_base_url: str = "http://localhost:8091/v1"
    embedding_api_key: SecretStr | None = None
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_timeout_seconds: float = Field(default=30, gt=0)
    embedding_batch_size: int = Field(default=32, ge=1, le=256)
    # E5 models expect these prefixes; set both to empty for models that do not use them.
    embedding_query_prefix: str = "query: "
    embedding_passage_prefix: str = "passage: "
    rag_min_score: float = Field(default=0.80, ge=0, le=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
