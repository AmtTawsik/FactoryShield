from sqlalchemy import ColumnElement, delete, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate
from app.modules.knowledge.models import KnowledgeCategory, KnowledgeChunk, KnowledgeDocument
from app.modules.knowledge.schemas import KnowledgeDocumentFilters, KnowledgeSearchResult


def _visible(factory_ids: frozenset[int] | None) -> ColumnElement[bool]:
    """General documents (no factory) for everyone; factory documents only within `factory_ids` (None = all)."""
    if factory_ids is None:
        return true()
    return or_(KnowledgeDocument.factory_id.is_(None), KnowledgeDocument.factory_id.in_(factory_ids))


class KnowledgeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, *objects: KnowledgeDocument | KnowledgeChunk) -> None:
        self.session.add_all(objects)

    async def get_by_source_key(self, source_key: str) -> KnowledgeDocument | None:
        return await self.session.scalar(select(KnowledgeDocument).where(KnowledgeDocument.source_key == source_key))

    async def delete_chunks(self, document_id: int) -> None:
        await self.session.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id))

    async def get(self, document_id: int) -> KnowledgeDocument | None:
        return await self.session.get(KnowledgeDocument, document_id)

    async def list_documents(
        self, filters: KnowledgeDocumentFilters, factory_ids: frozenset[int] | None
    ) -> tuple[list[KnowledgeDocument], int]:
        query = select(KnowledgeDocument).where(_visible(factory_ids))
        if filters.search:
            query = query.where(
                or_(
                    KnowledgeDocument.title.icontains(filters.search, autoescape=True),
                    KnowledgeDocument.source_authority.icontains(filters.search, autoescape=True),
                )
            )
        if filters.category:
            query = query.where(KnowledgeDocument.category == filters.category)
        if filters.content_status:
            query = query.where(KnowledgeDocument.content_status == filters.content_status)
        if filters.factory_id is not None:
            query = query.where(KnowledgeDocument.factory_id == filters.factory_id)
        return await paginate(self.session, query.order_by(KnowledgeDocument.title, KnowledgeDocument.id), filters)

    async def chunk_counts(self, document_ids: list[int]) -> dict[int, int]:
        rows = await self.session.execute(
            select(KnowledgeChunk.document_id, func.count())
            .where(KnowledgeChunk.document_id.in_(document_ids))
            .group_by(KnowledgeChunk.document_id)
        )
        return {document_id: count for document_id, count in rows}

    async def delete(self, document: KnowledgeDocument) -> None:
        # Chunks are removed by the ON DELETE CASCADE foreign key.
        await self.session.delete(document)

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
            .where(distance <= 1 - min_score, _visible(factory_ids))
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
