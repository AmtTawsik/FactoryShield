from typing import Annotated

from fastapi import Depends

from app.core.dependencies import DbSession
from app.modules.auth.repository import UserRepository
from app.modules.factories.dependencies import get_factory_service
from app.modules.inspections.repository import InspectionRepository
from app.modules.inspections.service import InspectionService


def get_inspection_service(session: DbSession) -> InspectionService:
    return InspectionService(
        session, InspectionRepository(session), get_factory_service(session), UserRepository(session)
    )


InspectionServiceDep = Annotated[InspectionService, Depends(get_inspection_service)]
