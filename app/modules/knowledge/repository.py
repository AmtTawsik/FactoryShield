from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge.models import KnowledgeCategory, KnowledgeChunk, KnowledgeDocument
from app.modules.knowledge.schemas import KnowledgeSearchResult


class KnowledgeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, *objects: KnowledgeDocument | KnowledgeChunk) -> None:
        self.session.add_all(objects)

    async def search(
        self,
        embedding: list[float],
        factory_ids: frozenset[int] | None,
        *,
        limit: int,
        min_score: float,
        category: KnowledgeCategory | None = None,
    ) -> list[KnowledgeSearchResult]:
        """Closest chunks by cosine similarity (1 = same direction), best first, above `min_score`.

        General documents (no factory) are visible to everyone; factory documents only within `factory_ids`
        (`None` means every factory).
        """
        distance = KnowledgeChunk.embedding.cosine_distance(embedding)
        query = (
            select(KnowledgeChunk, KnowledgeDocument, (1 - distance).label("score"))
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
            .where(distance <= 1 - min_score)
        )
        if factory_ids is not None:
            query = query.where(
                or_(KnowledgeDocument.factory_id.is_(None), KnowledgeDocument.factory_id.in_(factory_ids))
            )
        if category:
            query = query.where(KnowledgeDocument.category == category)
        query = query.order_by(distance, KnowledgeChunk.id).limit(limit)

        return [
            KnowledgeSearchResult(
                chunk_id=chunk.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=round(score, 4),
                document_id=document.id,
                title=document.title,
                source_authority=document.source_authority,
                source_url=document.source_url,
                category=document.category,
                content_status=document.content_status,
                verified_on=document.verified_on,
                factory_id=document.factory_id,
                created_at=document.created_at,
            )
            for chunk, document, score in await self.session.execute(query)
        ]
