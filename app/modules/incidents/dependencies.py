from typing import Annotated

from fastapi import Depends

from app.core.dependencies import DbSession
from app.modules.factories.repository import FactoryRepository
from app.modules.incidents.repository import IncidentRepository
from app.modules.incidents.service import IncidentService


def get_incident_service(session: DbSession) -> IncidentService:
    return IncidentService(session, IncidentRepository(session), FactoryRepository(session))


IncidentServiceDep = Annotated[IncidentService, Depends(get_incident_service)]
