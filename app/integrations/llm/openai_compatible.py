import logging

import openai
from openai import AsyncOpenAI

from app.integrations.llm.errors import LLMTimeoutError, LLMUnavailableError
from app.integrations.llm.schemas import ChatMessage, LLMResponse, ToolCall, ToolDefinition

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider:

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

    async def complete(self, messages: list[ChatMessage], tools: tuple[ToolDefinition, ...] = ()) -> LLMResponse:
        request = {"model": self.model, "messages": [_to_api_message(message) for message in messages]}
        if tools:
            request["tools"] = [_to_api_tool(tool) for tool in tools]
        try:
            response = await self._client.chat.completions.create(**request)
        except openai.APITimeoutError as exc:
            logger.warning("LLM request timed out (model %s)", self.model)
            raise LLMTimeoutError() from exc
        except openai.RateLimitError as exc:
            logger.warning("LLM rate limit reached (model %s)", self.model)
            raise LLMUnavailableError("AI assistant is busy, please try again shortly") from exc
        except openai.OpenAIError as exc:
            logger.error("LLM provider error (model %s): %s", self.model, exc)
            raise LLMUnavailableError() from exc

        message = response.choices[0].message if response.choices else None
        content = (message.content or "").strip() if message else ""
        tool_calls = _read_tool_calls(message)
        if not content and not tool_calls:
            logger.error("LLM returned an empty reply (model %s)", self.model)
            raise LLMUnavailableError()
        return LLMResponse(content=content or None, tool_calls=tool_calls)


def _to_api_message(message: ChatMessage) -> dict:
    data = {"role": message.role, "content": message.content}
    if message.tool_calls:
        data["tool_calls"] = [
            {"id": call.id, "type": "function", "function": {"name": call.name, "arguments": call.arguments}}
            for call in message.tool_calls
        ]
    if message.tool_call_id:
        data["tool_call_id"] = message.tool_call_id
    return data


def _to_api_tool(tool: ToolDefinition) -> dict:
    return {
        "type": "function",
        "function": {"name": tool.name, "description": tool.description, "parameters": tool.parameters},
    }


def _read_tool_calls(message) -> tuple[ToolCall, ...]:
    calls = []
    for index, call in enumerate(getattr(message, "tool_calls", None) or []):
        function = getattr(call, "function", None)
        if function is None:
            continue
        # some providers send an empty id
        calls.append(ToolCall(id=call.id or f"call_{index}", name=function.name, arguments=function.arguments or "{}"))
    return tuple(calls)
