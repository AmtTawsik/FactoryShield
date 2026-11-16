from typing import Annotated

from fastapi import Depends

from app.core.dependencies import DbSession
from app.modules.factories.repository import FactoryRepository
from app.modules.factories.service import FactoryService


def get_factory_service(session: DbSession) -> FactoryService:
    return FactoryService(session, FactoryRepository(session))


FactoryServiceDep = Annotated[FactoryService, Depends(get_factory_service)]
