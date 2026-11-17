import logging

import openai
from openai import AsyncOpenAI

from app.integrations.llm.errors import LLMTimeoutError, LLMUnavailableError
from app.integrations.llm.schemas import ChatMessage

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider:
    """Chat completions over any OpenAI-compatible API (OpenRouter by default)."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float,
        max_retries: int,
        http_client=None,
    ):
        self.model = model
        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
        )

    async def complete(self, messages: list[ChatMessage]) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": message.role, "content": message.content} for message in messages],
            )
        except openai.APITimeoutError as exc:
            logger.warning("LLM request timed out (model %s)", self.model)
            raise LLMTimeoutError() from exc
        except openai.RateLimitError as exc:
            logger.warning("LLM rate limit reached (model %s)", self.model)
            raise LLMUnavailableError("AI assistant is busy, please try again shortly") from exc
        except openai.OpenAIError as exc:
            logger.error("LLM provider error (model %s): %s", self.model, exc)
            raise LLMUnavailableError() from exc

        content = response.choices[0].message.content if response.choices else None
        if not content or not content.strip():
            logger.error("LLM returned an empty reply (model %s)", self.model)
            raise LLMUnavailableError()
        return content.strip()
