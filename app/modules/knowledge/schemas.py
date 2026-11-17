from datetime import date, datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.core.schemas import Id
from app.modules.knowledge.models import ContentStatus, KnowledgeCategory


class IngestStatus(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


class KnowledgeDocumentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    source_key: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{1,99}$", examples=["bd-labour-act-2006-chapter-6-safety"])
    title: str = Field(min_length=3, max_length=200)
    source_authority: str = Field(
        min_length=2, max_length=200, examples=["Department of Inspection for Factories and Establishments (DIFE)"]
    )
    source_url: HttpUrl | None = None
    category: KnowledgeCategory
    content_status: ContentStatus = ContentStatus.GENERAL_GUIDANCE
    verified_on: date | None = None
    factory_id: Id | None = Field(default=None, description="Set only for knowledge that belongs to one factory")

    @model_validator(mode="after")
    def official_needs_source(self) -> Self:
        if self.content_status == ContentStatus.OFFICIAL_VERIFIED and (
            self.source_url is None or self.verified_on is None
        ):
            raise ValueError("official_verified content needs source_url and verified_on")
        return self


class KnowledgeDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_key: str
    title: str
    source_authority: str
    source_url: str | None
    category: KnowledgeCategory
    content_status: ContentStatus
    verified_on: date | None
    factory_id: int | None
    created_at: datetime


class IngestResult(BaseModel):
    document: KnowledgeDocumentResponse
    status: IngestStatus
    chunk_count: int


class KnowledgeSource(BaseModel):
    """A stored document an answer drew on; every field comes from the database, never from the model."""

    document_id: int
    title: str
    source_authority: str
    source_url: str | None
    content_status: ContentStatus
    verified_on: date | None


class KnowledgeSearchResult(BaseModel):
    chunk_id: int
    chunk_index: int
    content: str
    score: float
    document_id: int
    title: str
    source_authority: str
    source_url: str | None
    category: KnowledgeCategory
    content_status: ContentStatus
    verified_on: date | None
    factory_id: int | None
    created_at: datetime
