from enum import StrEnum
from functools import lru_cache

from pydantic import EmailStr, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderName(StrEnum):
    GROQ = "groq"
    OPENROUTER = "openrouter"


# OpenAI-compatible chat completions endpoint of each provider.
LLM_BASE_URLS = {
    LLMProviderName.GROQ: "https://api.groq.com/openai/v1",
    LLMProviderName.OPENROUTER: "https://openrouter.ai/api/v1",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    app_name: str = "FactoryShield AI"
    environment: str = "development"

    database_url: str = Field(pattern=r"^postgresql\+asyncpg://")
    database_connect_timeout: int = Field(default=5, gt=0)

    jwt_secret_key: str = Field(min_length=32)
    jwt_expire_minutes: int = Field(default=60, gt=0)

    # The AI assistant uses one provider, chosen with LLM_PROVIDER. Without that provider's API key the app
    # still runs and only the AI assistant returns 503.
    llm_provider: LLMProviderName = LLMProviderName.GROQ
    groq_api_key: SecretStr | None = None
    groq_model: str = "openai/gpt-oss-120b"
    openrouter_api_key: SecretStr | None = None
    openrouter_model: str = "nvidia/nemotron-3.5-super-vl:free"
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
    # Calibrated on the sample documents: related questions (Bangla and English) scored 0.811 or more,
    # unrelated ones at most 0.787. Topic-adjacent questions can score above it; the prompt covers those.
    rag_min_score: float = Field(default=0.80, ge=0, le=1)

    # The MCP stdio server runs on the local machine as this existing, active user (roles and factory scope apply).
    mcp_stdio_user_email: EmailStr | None = None

    @property
    def llm_base_url(self) -> str:
        return LLM_BASE_URLS[self.llm_provider]

    @property
    def llm_api_key(self) -> SecretStr | None:
        return getattr(self, f"{self.llm_provider.value}_api_key")

    @property
    def llm_model(self) -> str:
        return getattr(self, f"{self.llm_provider.value}_model")

    @field_validator("mcp_stdio_user_email", mode="before")
    @classmethod
    def blank_is_unset(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value


@lru_cache
def get_settings() -> Settings:
    return Settings()
