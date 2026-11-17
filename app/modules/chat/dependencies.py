from typing import Annotated

from fastapi import Depends

from app.core.config import get_settings
from app.core.dependencies import DbSession
from app.integrations.embeddings.client import EmbeddingClient, get_embedding_client
from app.integrations.llm.client import LLMClient, get_llm_client
from app.modules.chat.repository import ChatRepository, FactoryContextRepository
from app.modules.chat.service import ChatService
from app.modules.chat.tools import ChatTools
from app.modules.corrective_actions.dependencies import get_action_service
from app.modules.factories.dependencies import get_factory_service
from app.modules.incidents.dependencies import get_incident_service
from app.modules.inspections.dependencies import get_inspection_service
from app.modules.knowledge.repository import KnowledgeRepository
from app.modules.knowledge.service import KnowledgeService


def get_chat_service(
    session: DbSession, embeddings: Annotated[EmbeddingClient, Depends(get_embedding_client)]
) -> ChatService:
    factories = get_factory_service(session)
    tools = ChatTools(
        factories, get_inspection_service(session), get_action_service(session), get_incident_service(session)
    )
    knowledge = KnowledgeService(
        session, KnowledgeRepository(session), factories, embeddings, get_settings().rag_min_score
    )
    return ChatService(session, ChatRepository(session), FactoryContextRepository(session), factories, tools, knowledge)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]
