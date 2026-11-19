from datetime import date
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, CreatedAtMixin, TimestampMixin, string_enum
from app.integrations.embeddings.client import EMBEDDING_DIMENSIONS
from app.modules.factories.models import Factory


class KnowledgeCategory(StrEnum):
    LABOUR_LAW = "labour_law"
    FIRE_SAFETY = "fire_safety"
    ELECTRICAL_SAFETY = "electrical_safety"
    BUILDING_SAFETY = "building_safety"
    CHEMICAL_SAFETY = "chemical_safety"
    OCCUPATIONAL_HEALTH = "occupational_health"
    INCIDENT_HANDLING = "incident_handling"
    INSPECTION = "inspection"
    FACTORY_PROCEDURE = "factory_procedure"


class ContentStatus(StrEnum):
    OFFICIAL_VERIFIED = "official_verified"
    GENERAL_GUIDANCE = "general_guidance"


class KnowledgeDocument(TimestampMixin, Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        CheckConstraint("factory_id IS NULL OR organization_id IS NOT NULL", name="factory_document_has_organization"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_key: Mapped[str] = mapped_column(String(100), unique=True)
    content_hash: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(200))
    source_authority: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(String(500))
    category: Mapped[KnowledgeCategory] = mapped_column(string_enum(KnowledgeCategory, "knowledge_category"), index=True)
    content_status: Mapped[ContentStatus] = mapped_column(string_enum(ContentStatus, "content_status"))
    verified_on: Mapped[date | None] = mapped_column(Date)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), index=True)
    factory_id: Mapped[int | None] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), index=True)

    factory: Mapped[Factory | None] = relationship()


class KnowledgeChunk(CreatedAtMixin, Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_knowledge_chunks_document_id_chunk_index"),
        Index(
            "ix_knowledge_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"))
    chunk_index: Mapped[int]
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS))

    document: Mapped[KnowledgeDocument] = relationship()
