from functools import lru_cache

from app.core.config import get_settings
from app.integrations.llm.errors import LLMNotConfiguredError
from app.integrations.llm.openai_compatible import OpenAICompatibleProvider
from app.integrations.llm.prompts import SYSTEM_PROMPT
from app.integrations.llm.schemas import ChatMessage, LLMProvider, LLMResponse, ToolDefinition


class LLMClient:
    """Adds the FactoryShield system prompt and sends the conversation to the provider."""

    def __init__(self, provider: LLMProvider, system_prompt: str = SYSTEM_PROMPT):
        self.provider = provider
        self.system_prompt = system_prompt

    async def complete(self, messages: list[ChatMessage], tools: tuple[ToolDefinition, ...] = ()) -> LLMResponse:
        return await self.provider.complete([ChatMessage("system", self.system_prompt), *messages], tools)


@lru_cache
def get_llm_client() -> LLMClient:
    settings = get_settings()
    api_key = settings.llm_api_key.get_secret_value().strip() if settings.llm_api_key else ""
    if not api_key:
        raise LLMNotConfiguredError()

    provider = OpenAICompatibleProvider(
        base_url=settings.llm_base_url,
        api_key=api_key,
        model=settings.llm_model,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )
    return LLMClient(provider, settings.llm_system_prompt or SYSTEM_PROMPT)
