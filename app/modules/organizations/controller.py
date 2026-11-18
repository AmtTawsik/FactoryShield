from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.pagination import Page
from app.core.schemas import IdPath
from app.modules.auth.dependencies import SuperAdminUser
from app.modules.organizations.dependencies import OrganizationServiceDep
from app.modules.organizations.schemas import (
    AdminAccountCreate,
    OrganizationCreate,
    OrganizationDetail,
    OrganizationFilters,
    OrganizationItem,
    OrganizationUpdate,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=Page[OrganizationItem])
async def list_organizations(
    filters: Annotated[OrganizationFilters, Query()], admin: SuperAdminUser, service: OrganizationServiceDep
):
    return await service.list(filters)


@router.get("/{organization_id}", response_model=OrganizationDetail)
async def get_organization(organization_id: IdPath, admin: SuperAdminUser, service: OrganizationServiceDep):
    return await service.get(organization_id)


@router.post("", response_model=OrganizationDetail, status_code=status.HTTP_201_CREATED)
async def create_organization(data: OrganizationCreate, admin: SuperAdminUser, service: OrganizationServiceDep):
    return await service.create(data)


@router.patch("/{organization_id}", response_model=OrganizationDetail)
async def update_organization(
    organization_id: IdPath, data: OrganizationUpdate, admin: SuperAdminUser, service: OrganizationServiceDep
):
    return await service.update(organization_id, data)


@router.post("/{organization_id}/admins", response_model=OrganizationDetail, status_code=status.HTTP_201_CREATED)
async def add_organization_admin(
    organization_id: IdPath, data: AdminAccountCreate, admin: SuperAdminUser, service: OrganizationServiceDep
):
    return await service.add_admin(organization_id, data)
