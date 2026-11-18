from typing import Annotated

from fastapi import APIRouter, Form, Query, UploadFile, status

from app.core.pagination import Page
from app.core.schemas import IdPath
from app.modules.auth.dependencies import AdminUser, CurrentFactoryScope
from app.modules.knowledge.dependencies import KnowledgeServiceDep
from app.modules.knowledge.schemas import (
    IngestResult,
    KnowledgeDocumentFilters,
    KnowledgeDocumentItem,
    KnowledgeDocumentMetadata,
)
from app.modules.knowledge.service import MAX_UPLOAD_BYTES

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/documents", response_model=Page[KnowledgeDocumentItem])
async def list_documents(
    filters: Annotated[KnowledgeDocumentFilters, Query()], scope: CurrentFactoryScope, service: KnowledgeServiceDep
):
    return await service.list_documents(filters, scope)


@router.post("/documents", response_model=IngestResult, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    metadata: Annotated[KnowledgeDocumentMetadata, Form()],
    admin: AdminUser,
    scope: CurrentFactoryScope,
    service: KnowledgeServiceDep,
):
    # One byte over the limit is enough to reject the file without reading all of it.
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    return await service.upload(file.filename or "", data, metadata, scope)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: IdPath, admin: AdminUser, scope: CurrentFactoryScope, service: KnowledgeServiceDep
):
    await service.delete_document(document_id, scope)
