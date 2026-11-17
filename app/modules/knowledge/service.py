import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InvalidDataError
from app.integrations.embeddings.client import EmbeddingClient
from app.modules.auth.service import FactoryScope
from app.modules.factories.service import FactoryService
from app.modules.knowledge.models import KnowledgeCategory, KnowledgeChunk, KnowledgeDocument
from app.modules.knowledge.repository import KnowledgeRepository
from app.modules.knowledge.schemas import (
    IngestResult,
    IngestStatus,
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    KnowledgeSearchResult,
)

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

    async def ingest(self, data: KnowledgeDocumentCreate, chunks: list[str], scope: FactoryScope) -> IngestResult:
        """Saves a document and its embedded chunks, or updates the document already stored under the same key.

        Unchanged chunks are not embedded again; changed chunks replace the old ones.
        """
        texts = [chunk.strip() for chunk in chunks]
        if not texts or not all(texts):
            raise InvalidDataError("A document needs at least one non-empty chunk")
        if data.factory_id is not None:
            await self.factories.get(data.factory_id, scope)
        document = await self.knowledge.get_by_source_key(data.source_key)
        if document is not None and document.factory_id is not None:
            # Only users who can see a factory's document may replace it.
            await self.factories.get(document.factory_id, scope)

        values = data.model_dump()
        values["source_url"] = str(data.source_url) if data.source_url else None
        content_hash = _content_hash(self.embeddings.model, texts)

        if document is not None and document.content_hash == content_hash:
            changed = {field: value for field, value in values.items() if getattr(document, field) != value}
            if not changed:
                return _result(document, status=IngestStatus.UNCHANGED, chunk_count=len(texts))
            for field, value in changed.items():
                setattr(document, field, value)
            await self.session.commit()
            await self.session.refresh(document)
            return _result(document, status=IngestStatus.UPDATED, chunk_count=len(texts))

        # Embed first: if the service fails, nothing is written or replaced.
        vectors = await self.embeddings.embed_passages(texts)
        if document is None:
            document = KnowledgeDocument(**values, content_hash=content_hash)
            self.knowledge.add(document)
            await self.session.flush()
            status = IngestStatus.CREATED
        else:
            for field, value in values.items():
                setattr(document, field, value)
            document.content_hash = content_hash
            await self.knowledge.delete_chunks(document.id)
            status = IngestStatus.UPDATED
        self.knowledge.add(
            *(
                KnowledgeChunk(document_id=document.id, chunk_index=index, content=text, embedding=vector)
                for index, (text, vector) in enumerate(zip(texts, vectors, strict=True))
            )
        )
        await self.session.commit()
        await self.session.refresh(document)
        return _result(document, status=status, chunk_count=len(texts))

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


def _content_hash(model: str, texts: list[str]) -> str:
    digest = hashlib.sha256(model.encode())
    for text in texts:
        # The separator keeps ["ab", "c"] and ["a", "bc"] apart.
        digest.update(b"\x00" + text.encode())
    return digest.hexdigest()


def _result(document: KnowledgeDocument, status: IngestStatus, chunk_count: int) -> IngestResult:
    return IngestResult(
        document=KnowledgeDocumentResponse.model_validate(document), status=status, chunk_count=chunk_count
    )
