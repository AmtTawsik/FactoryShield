from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.pagination import PageParams
from app.core.schemas import Id
from app.modules.chat.models import MessageRole
from app.modules.knowledge.schemas import KnowledgeSource

MAX_MESSAGE_LENGTH = 4000
MAX_PREVIOUS_MESSAGES = 20


class PreviousMessage(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    role: MessageRole
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)
    conversation_id: Id | None = None
    factory_id: Id | None = Field(default=None, description="Only when starting a new conversation")
    previous_messages: list[PreviousMessage] = Field(
        default_factory=list,
        max_length=MAX_PREVIOUS_MESSAGES,
        description="Earlier turns to start a new conversation with, oldest first",
    )

    @model_validator(mode="after")
    def new_conversation_fields_only(self) -> Self:
        if self.conversation_id is not None:
            if self.factory_id is not None:
                raise ValueError("factory_id can only be set when starting a new conversation")
            if self.previous_messages:
                raise ValueError("previous_messages can only be sent when starting a new conversation")
        return self


class ChatResponse(BaseModel):
    conversation_id: int
    factory_id: int | None
    reply: str
    tools_used: list[str] = Field(default_factory=list, description="Tools the assistant called for this answer")
    sources: list[KnowledgeSource] = Field(
        default_factory=list,
        description="Documents found by the document search for this message, in the order given to the assistant",
    )


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: MessageRole
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    factory_id: int | None
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse]


class ConversationFilters(PageParams):
    factory_id: Id | None = None
