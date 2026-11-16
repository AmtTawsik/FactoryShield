from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.pagination import Page
from app.modules.auth.dependencies import AdminUser, CurrentFactoryScope
from app.modules.factories.dependencies import FactoryServiceDep
from app.modules.factories.schemas import FactoryCreate, FactoryFilters, FactoryResponse, FactoryUpdate

router = APIRouter(prefix="/factories", tags=["factories"])


@router.get("", response_model=Page[FactoryResponse])
async def list_factories(
    filters: Annotated[FactoryFilters, Query()], scope: CurrentFactoryScope, service: FactoryServiceDep
):
    return await service.list(filters, scope)


@router.get("/{factory_id}", response_model=FactoryResponse)
async def get_factory(factory_id: int, scope: CurrentFactoryScope, service: FactoryServiceDep):
    return await service.get(factory_id, scope)


@router.post("", response_model=FactoryResponse, status_code=status.HTTP_201_CREATED)
async def create_factory(data: FactoryCreate, admin: AdminUser, service: FactoryServiceDep):
    return await service.create(data)


@router.patch("/{factory_id}", response_model=FactoryResponse)
async def update_factory(
    factory_id: int, data: FactoryUpdate, admin: AdminUser, scope: CurrentFactoryScope, service: FactoryServiceDep
):
    return await service.update(factory_id, data, scope)


@router.delete("/{factory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_factory(factory_id: int, admin: AdminUser, scope: CurrentFactoryScope, service: FactoryServiceDep):
    await service.delete(factory_id, scope)
