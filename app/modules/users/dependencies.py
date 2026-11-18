from typing import Annotated

from fastapi import Depends

from app.core.dependencies import DbSession
from app.modules.auth.repository import UserRepository
from app.modules.users.repository import UserAdminRepository
from app.modules.users.service import UserService


def get_user_service(session: DbSession) -> UserService:
    return UserService(session, UserRepository(session), UserAdminRepository(session))


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
