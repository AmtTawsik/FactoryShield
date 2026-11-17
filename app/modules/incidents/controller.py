from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.pagination import Page
from app.core.schemas import IdPath
from app.modules.auth.dependencies import AdminUser, CurrentFactoryScope
from app.modules.incidents.dependencies import IncidentServiceDep
from app.modules.incidents.schemas import IncidentCreate, IncidentFilters, IncidentResponse, IncidentUpdate

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=Page[IncidentResponse])
async def list_incidents(
    filters: Annotated[IncidentFilters, Query()], scope: CurrentFactoryScope, service: IncidentServiceDep
):
    return await service.list(filters, scope)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: IdPath, scope: CurrentFactoryScope, service: IncidentServiceDep):
    return await service.get(incident_id, scope)


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    data: IncidentCreate, admin: AdminUser, scope: CurrentFactoryScope, service: IncidentServiceDep
):
    return await service.create(data, admin, scope)


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: IdPath, data: IncidentUpdate, admin: AdminUser, scope: CurrentFactoryScope, service: IncidentServiceDep
):
    return await service.update(incident_id, data, scope)


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(incident_id: IdPath, admin: AdminUser, scope: CurrentFactoryScope, service: IncidentServiceDep):
    await service.delete(incident_id, scope)
