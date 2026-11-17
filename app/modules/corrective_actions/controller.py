from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.pagination import Page
from app.core.schemas import IdPath
from app.modules.auth.dependencies import AdminUser, CurrentFactoryScope
from app.modules.corrective_actions.dependencies import ActionServiceDep
from app.modules.corrective_actions.schemas import ActionCreate, ActionFilters, ActionResponse, ActionUpdate

router = APIRouter(prefix="/corrective-actions", tags=["corrective-actions"])


@router.get("", response_model=Page[ActionResponse])
async def list_actions(filters: Annotated[ActionFilters, Query()], scope: CurrentFactoryScope, service: ActionServiceDep):
    return await service.list(filters, scope)


@router.get("/{action_id}", response_model=ActionResponse)
async def get_action(action_id: IdPath, scope: CurrentFactoryScope, service: ActionServiceDep):
    return await service.get(action_id, scope)


@router.post("", response_model=ActionResponse, status_code=status.HTTP_201_CREATED)
async def create_action(data: ActionCreate, admin: AdminUser, scope: CurrentFactoryScope, service: ActionServiceDep):
    return await service.create(data, scope)


@router.patch("/{action_id}", response_model=ActionResponse)
async def update_action(
    action_id: IdPath, data: ActionUpdate, admin: AdminUser, scope: CurrentFactoryScope, service: ActionServiceDep
):
    return await service.update(action_id, data, scope)


@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action(action_id: IdPath, admin: AdminUser, scope: CurrentFactoryScope, service: ActionServiceDep):
    await service.delete(action_id, scope)
