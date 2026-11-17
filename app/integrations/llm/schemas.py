from dataclasses import dataclass
from typing import Literal, Protocol

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


class LLMProvider(Protocol):
    """Anything that turns a list of messages into a reply. Provider-specific code implements this."""

    async def complete(self, messages: list[ChatMessage]) -> str: ...
