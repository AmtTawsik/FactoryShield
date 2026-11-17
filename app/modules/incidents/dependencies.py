from typing import Annotated

from fastapi import Depends

from app.core.dependencies import DbSession
from app.modules.factories.dependencies import get_factory_service
from app.modules.incidents.repository import IncidentRepository
from app.modules.incidents.service import IncidentService


def get_incident_service(session: DbSession) -> IncidentService:
    return IncidentService(session, IncidentRepository(session), get_factory_service(session))


IncidentServiceDep = Annotated[IncidentService, Depends(get_incident_service)]
