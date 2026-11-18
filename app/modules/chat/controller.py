from typing import Annotated

from fastapi import APIRouter, Query

from app.core.pagination import Page
from app.core.schemas import IdPath
from app.modules.auth.dependencies import CurrentFactoryScope, CurrentUser
from app.modules.chat.dependencies import ChatServiceDep, LLMClientDep
from app.modules.chat.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationFilters,
    ConversationResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def send_message(
    data: ChatRequest, user: CurrentUser, scope: CurrentFactoryScope, llm: LLMClientDep, service: ChatServiceDep
):
    return await service.send(data, user, scope, llm)


@router.get("/conversations", response_model=Page[ConversationResponse])
async def list_conversations(
    filters: Annotated[ConversationFilters, Query()],
    user: CurrentUser,
    scope: CurrentFactoryScope,
    service: ChatServiceDep,
):
    return await service.list(filters, user, scope)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: IdPath, user: CurrentUser, scope: CurrentFactoryScope, service: ChatServiceDep
):
    return await service.get(conversation_id, user, scope)
