from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InvalidDataError
from app.integrations.embeddings.client import EmbeddingClient
from app.modules.auth.service import FactoryScope
from app.modules.factories.service import FactoryService
from app.modules.knowledge.models import KnowledgeCategory, KnowledgeChunk, KnowledgeDocument
from app.modules.knowledge.repository import KnowledgeRepository
from app.modules.knowledge.schemas import KnowledgeDocumentCreate, KnowledgeSearchResult

MAX_RESULTS = 10


class KnowledgeService:
    def __init__(
        self,
        session: AsyncSession,
        knowledge: KnowledgeRepository,
        factories: FactoryService,
        embeddings: EmbeddingClient,
        min_score: float,
    ):
        self.session = session
        self.knowledge = knowledge
        self.factories = factories
        self.embeddings = embeddings
        self.min_score = min_score

    async def store_document(
        self, data: KnowledgeDocumentCreate, chunks: list[str], scope: FactoryScope
    ) -> KnowledgeDocument:
        """Embeds the chunks with the embedding service and saves the document and its chunks together."""
        texts = [chunk.strip() for chunk in chunks]
        if not texts or not all(texts):
            raise InvalidDataError("A document needs at least one non-empty chunk")
        if data.factory_id is not None:
            await self.factories.get(data.factory_id, scope)

        # Embed first: if the service fails, nothing is written.
        vectors = await self.embeddings.embed_passages(texts)
        values = data.model_dump()
        values["source_url"] = str(data.source_url) if data.source_url else None
        document = KnowledgeDocument(**values)
        self.knowledge.add(document)
        await self.session.flush()
        self.knowledge.add(
            *(
                KnowledgeChunk(document_id=document.id, chunk_index=index, content=text, embedding=vector)
                for index, (text, vector) in enumerate(zip(texts, vectors, strict=True))
            )
        )
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def search(
        self,
        query: str,
        scope: FactoryScope,
        *,
        limit: int = 5,
        category: KnowledgeCategory | None = None,
    ) -> list[KnowledgeSearchResult]:
        """Chunks most similar to the question that the user may see. An empty list means nothing relevant."""
        text = query.strip()
        if not text:
            raise InvalidDataError("Search query cannot be empty")
        embedding = await self.embeddings.embed_query(text)
        return await self.knowledge.search(
            embedding,
            scope.factory_ids,
            limit=max(1, min(limit, MAX_RESULTS)),
            min_score=self.min_score,
            category=category,
        )
