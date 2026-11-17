from typing import Annotated

from fastapi import Depends

from app.core.dependencies import DbSession
from app.modules.corrective_actions.repository import ActionRepository
from app.modules.corrective_actions.service import ActionService
from app.modules.factories.dependencies import get_factory_service
from app.modules.incidents.repository import IncidentRepository
from app.modules.inspections.repository import InspectionRepository


def get_action_service(session: DbSession) -> ActionService:
    return ActionService(
        session,
        ActionRepository(session),
        get_factory_service(session),
        InspectionRepository(session),
        IncidentRepository(session),
    )


ActionServiceDep = Annotated[ActionService, Depends(get_action_service)]
