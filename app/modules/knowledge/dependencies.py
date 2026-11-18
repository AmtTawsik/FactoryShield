from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import DbSession
from app.integrations.embeddings.client import EmbeddingClient, get_embedding_client
from app.modules.factories.dependencies import get_factory_service
from app.modules.knowledge.repository import KnowledgeRepository
from app.modules.knowledge.service import KnowledgeService


def build_knowledge_service(session: AsyncSession, embeddings: EmbeddingClient) -> KnowledgeService:
    return KnowledgeService(
        session,
        KnowledgeRepository(session),
        get_factory_service(session),
        embeddings,
        get_settings().rag_min_score,
    )


def get_knowledge_service(
    session: DbSession, embeddings: Annotated[EmbeddingClient, Depends(get_embedding_client)]
) -> KnowledgeService:
    return build_knowledge_service(session, embeddings)


KnowledgeServiceDep = Annotated[KnowledgeService, Depends(get_knowledge_service)]
