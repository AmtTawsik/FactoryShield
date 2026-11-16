from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.pagination import Page
from app.modules.auth.dependencies import AdminUser, CurrentFactoryScope
from app.modules.inspections.dependencies import InspectionServiceDep
from app.modules.inspections.schemas import (
    InspectionCreate,
    InspectionFilters,
    InspectionResponse,
    InspectionUpdate,
)

router = APIRouter(prefix="/inspections", tags=["inspections"])


@router.get("", response_model=Page[InspectionResponse])
async def list_inspections(
    filters: Annotated[InspectionFilters, Query()], scope: CurrentFactoryScope, service: InspectionServiceDep
):
    return await service.list(filters, scope)


@router.get("/{inspection_id}", response_model=InspectionResponse)
async def get_inspection(inspection_id: int, scope: CurrentFactoryScope, service: InspectionServiceDep):
    return await service.get(inspection_id, scope)


@router.post("", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
async def create_inspection(
    data: InspectionCreate, admin: AdminUser, scope: CurrentFactoryScope, service: InspectionServiceDep
):
    return await service.create(data, scope)


@router.patch("/{inspection_id}", response_model=InspectionResponse)
async def update_inspection(
    inspection_id: int,
    data: InspectionUpdate,
    admin: AdminUser,
    scope: CurrentFactoryScope,
    service: InspectionServiceDep,
):
    return await service.update(inspection_id, data, scope)


@router.delete("/{inspection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inspection(
    inspection_id: int, admin: AdminUser, scope: CurrentFactoryScope, service: InspectionServiceDep
):
    await service.delete(inspection_id, scope)
