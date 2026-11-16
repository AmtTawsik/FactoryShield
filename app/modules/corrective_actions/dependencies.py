from typing import Annotated

from fastapi import Depends

from app.core.dependencies import DbSession
from app.modules.corrective_actions.repository import ActionRepository
from app.modules.corrective_actions.service import ActionService
from app.modules.factories.repository import FactoryRepository
from app.modules.incidents.repository import IncidentRepository
from app.modules.inspections.repository import InspectionRepository


def get_action_service(session: DbSession) -> ActionService:
    return ActionService(
        session,
        ActionRepository(session),
        FactoryRepository(session),
        InspectionRepository(session),
        IncidentRepository(session),
    )


ActionServiceDep = Annotated[ActionService, Depends(get_action_service)]
