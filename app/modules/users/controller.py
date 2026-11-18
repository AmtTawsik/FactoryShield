from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.pagination import Page
from app.core.schemas import IdPath
from app.modules.auth.dependencies import AdminUser
from app.modules.users.dependencies import UserServiceDep
from app.modules.users.schemas import UserCreate, UserDetail, UserFactoriesUpdate, UserFilters, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Page[UserDetail])
async def list_users(filters: Annotated[UserFilters, Query()], admin: AdminUser, service: UserServiceDep):
    return await service.list(filters)


@router.get("/{user_id}", response_model=UserDetail)
async def get_user(user_id: IdPath, admin: AdminUser, service: UserServiceDep):
    return await service.get(user_id)


@router.post("", response_model=UserDetail, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, admin: AdminUser, service: UserServiceDep):
    return await service.create(data)


@router.patch("/{user_id}", response_model=UserDetail)
async def update_user(user_id: IdPath, data: UserUpdate, admin: AdminUser, service: UserServiceDep):
    return await service.update(user_id, data, admin)


@router.put("/{user_id}/factories", response_model=UserDetail)
async def set_user_factories(
    user_id: IdPath, data: UserFactoriesUpdate, admin: AdminUser, service: UserServiceDep
):
    return await service.set_factories(user_id, data.factory_ids)
