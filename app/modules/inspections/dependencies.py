from typing import Annotated

from fastapi import Depends

from app.core.dependencies import DbSession
from app.modules.auth.repository import UserRepository
from app.modules.factories.repository import FactoryRepository
from app.modules.inspections.repository import InspectionRepository
from app.modules.inspections.service import InspectionService


def get_inspection_service(session: DbSession) -> InspectionService:
    return InspectionService(
        session, InspectionRepository(session), FactoryRepository(session), UserRepository(session)
    )


InspectionServiceDep = Annotated[InspectionService, Depends(get_inspection_service)]
