import hashlib
import re
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ForbiddenError, InvalidDataError, NotFoundError
from app.core.pagination import Page
from app.integrations.embeddings.client import EmbeddingClient
from app.modules.auth.service import FactoryScope
from app.modules.factories.service import FactoryService
from app.modules.knowledge.ingestion import IngestionError, extract_text_from_bytes, split_into_chunks
from app.modules.knowledge.models import KnowledgeCategory, KnowledgeChunk, KnowledgeDocument
from app.modules.knowledge.repository import KnowledgeRepository
from app.modules.knowledge.schemas import (
    IngestResult,
    IngestStatus,
    KnowledgeDocumentCreate,
    KnowledgeDocumentFilters,
    KnowledgeDocumentItem,
    KnowledgeDocumentMetadata,
    KnowledgeDocumentResponse,
    KnowledgeSearchResult,
)

MAX_RESULTS = 10
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_SOURCE_KEY_LENGTH = 100


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
        texts = [chunk.strip() for chunk in chunks]
        if not texts or not all(texts):
            raise InvalidDataError("A document needs at least one non-empty chunk")
        if data.factory_id is not None:
            if scope.organization_id is None:
                raise InvalidDataError("Shared library documents cannot belong to a factory")
            await self.factories.get(data.factory_id, scope)
        document = await self.knowledge.get_by_source_key(data.source_key)
        if document is not None:
            if document.organization_id != scope.organization_id:
                raise ConflictError("A document with this key belongs to someone else")
            if document.factory_id is not None:
                await self.factories.get(document.factory_id, scope)

        values = data.model_dump()
        values["organization_id"] = scope.organization_id
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

        # embed first, so nothing is written if the service fails
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

    async def upload(
        self, file_name: str, data: bytes, metadata: KnowledgeDocumentMetadata, scope: FactoryScope
    ) -> IngestResult:
        if len(data) > MAX_UPLOAD_BYTES:
            raise InvalidDataError(f"The file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB")
        try:
            chunks = split_into_chunks(extract_text_from_bytes(file_name, data).text)
        except IngestionError as exc:
            raise InvalidDataError(str(exc)) from exc
        if not chunks:
            raise InvalidDataError(f"{file_name}: no text found")
        document = KnowledgeDocumentCreate(
            **metadata.model_dump(), source_key=_upload_key(file_name, scope.organization_id, metadata.factory_id)
        )
        return await self.ingest(document, chunks, scope)

    async def list_documents(
        self, filters: KnowledgeDocumentFilters, scope: FactoryScope
    ) -> Page[KnowledgeDocumentItem]:
        if filters.factory_id is not None:
            await self.factories.get(filters.factory_id, scope)
        documents, total = await self.knowledge.list_documents(filters, scope)
        counts = await self.knowledge.chunk_counts([document.id for document in documents])
        return Page(
            items=[
                KnowledgeDocumentItem(
                    **KnowledgeDocumentResponse.model_validate(document).model_dump(),
                    updated_at=document.updated_at,
                    chunk_count=counts.get(document.id, 0),
                )
                for document in documents
            ],
            total=total,
            page=filters.page,
            size=filters.size,
        )

    async def delete_document(self, document_id: int, scope: FactoryScope) -> None:
        document = await self.knowledge.get(document_id)
        visible = document is not None and (
            document.organization_id is None
            or (
                document.organization_id == scope.organization_id
                and (document.factory_id is None or scope.allows(document.factory_id))
            )
        )
        if not visible:
            raise NotFoundError("Document not found")
        if document.organization_id != scope.organization_id:
            raise ForbiddenError("Shared library documents are managed by the platform administrator")
        await self.knowledge.delete(document)
        await self.session.commit()

    async def search(
        self,
        query: str,
        scope: FactoryScope,
        *,
        limit: int = 5,
        category: KnowledgeCategory | None = None,
    ) -> list[KnowledgeSearchResult]:
        text = query.strip()
        if not text:
            raise InvalidDataError("Search query cannot be empty")
        embedding = await self.embeddings.embed_query(text)
        return await self.knowledge.search(
            embedding,
            scope,
            limit=max(1, min(limit, MAX_RESULTS)),
            min_score=self.min_score,
            category=category,
        )


def _upload_key(file_name: str, organization_id: int | None, factory_id: int | None) -> str:
    stem = Path(file_name).stem.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    if not slug:
        slug = hashlib.sha256(stem.encode()).hexdigest()[:16]
    prefix = "upload."
    if organization_id is not None:
        prefix += f"o{organization_id}."
    if factory_id is not None:
        prefix += f"f{factory_id}."
    room = MAX_SOURCE_KEY_LENGTH - len(prefix)
    if len(slug) > room:
        digest = hashlib.sha256(slug.encode()).hexdigest()[:16]
        slug = f"{slug[: room - len(digest) - 1].rstrip('-')}-{digest}"
    return prefix + slug


def _content_hash(model: str, texts: list[str]) -> str:
    digest = hashlib.sha256(model.encode())
    for text in texts:
        digest.update(b"\x00" + text.encode())
    return digest.hexdigest()


def _result(document: KnowledgeDocument, status: IngestStatus, chunk_count: int) -> IngestResult:
    return IngestResult(
        document=KnowledgeDocumentResponse.model_validate(document), status=status, chunk_count=chunk_count
    )
