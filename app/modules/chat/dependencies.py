from typing import Annotated

from fastapi import Depends

from app.core.dependencies import DbSession
from app.integrations.llm.client import LLMClient, get_llm_client
from app.modules.chat.repository import ChatRepository, FactoryContextRepository
from app.modules.chat.service import ChatService
from app.modules.factories.dependencies import get_factory_service


def get_chat_service(session: DbSession) -> ChatService:
    return ChatService(
        session, ChatRepository(session), FactoryContextRepository(session), get_factory_service(session)
    )


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]
