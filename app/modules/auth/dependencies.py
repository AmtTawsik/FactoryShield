from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.dependencies import DbSession
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.modules.auth.models import User, UserRole
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import AuthService, FactoryScope

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(session: DbSession) -> AuthService:
    return AuthService(session, UserRepository(session))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    service: AuthServiceDep,
) -> User:
    if credentials is None:
        raise UnauthorizedError("Not authenticated")
    user_id = decode_access_token(credentials.credentials)
    return await service.get_active_user(user_id)


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise ForbiddenError("Admin access required")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


async def require_super_admin(user: CurrentUser) -> User:
    if user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenError("Platform administrator access required")
    return user


SuperAdminUser = Annotated[User, Depends(require_super_admin)]


async def require_knowledge_manager(user: CurrentUser) -> User:
    if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise ForbiddenError("Admin access required")
    return user


KnowledgeManager = Annotated[User, Depends(require_knowledge_manager)]


async def get_factory_scope(user: CurrentUser, service: AuthServiceDep) -> FactoryScope:
    return await service.get_factory_scope(user)


CurrentFactoryScope = Annotated[FactoryScope, Depends(get_factory_scope)]


async def get_knowledge_scope(user: CurrentUser, service: AuthServiceDep) -> FactoryScope:
    return await service.get_knowledge_scope(user)


KnowledgeScope = Annotated[FactoryScope, Depends(get_knowledge_scope)]
