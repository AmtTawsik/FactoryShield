from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InvalidDataError, NotFoundError
from app.core.pagination import Page
from app.core.time import now, today
from app.modules.auth.service import FactoryScope
from app.modules.corrective_actions.models import ActionStatus, CorrectiveAction
from app.modules.corrective_actions.repository import ActionRepository
from app.modules.corrective_actions.schemas import ActionCreate, ActionFilters, ActionResponse, ActionUpdate
from app.modules.factories.service import FactoryService
from app.modules.incidents.repository import IncidentRepository
from app.modules.inspections.repository import InspectionRepository


class ActionService:
    def __init__(
        self,
        session: AsyncSession,
        actions: ActionRepository,
        factories: FactoryService,
        inspections: InspectionRepository,
        incidents: IncidentRepository,
    ):
        self.session = session
        self.actions = actions
        self.factories = factories
        self.inspections = inspections
        self.incidents = incidents

    async def list(self, filters: ActionFilters, scope: FactoryScope) -> Page[ActionResponse]:
        items, total = await self.actions.list(filters, scope.factory_ids, today())
        return Page(
            items=[ActionResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            size=filters.size,
        )

    async def get(self, action_id: int, scope: FactoryScope) -> CorrectiveAction:
        action = await self.actions.get(action_id)
        if action is None or not scope.allows(action.factory_id):
            raise NotFoundError("Corrective action not found")
        return action

    async def create(self, data: ActionCreate, scope: FactoryScope) -> CorrectiveAction:
        await self.factories.get(data.factory_id, scope)

        action = CorrectiveAction(**data.model_dump())
        await self._check_links(action)
        self._sync_completed_at(action)
        self.actions.add(action)
        await self.session.commit()
        await self.session.refresh(action)
        return action

    async def update(self, action_id: int, data: ActionUpdate, scope: FactoryScope) -> CorrectiveAction:
        action = await self.get(action_id, scope)
        for field, value in data.changes().items():
            setattr(action, field, value)
        self._sync_completed_at(action)
        await self._check_links(action)
        await self.session.commit()
        await self.session.refresh(action)
        return action

    async def delete(self, action_id: int, scope: FactoryScope) -> None:
        action = await self.get(action_id, scope)
        await self.actions.delete(action)
        await self.session.commit()

    async def _check_links(self, action: CorrectiveAction) -> None:
        # no autoflush, otherwise a missing link fails as a database error
        with self.session.no_autoflush:
            await self._check_link_values(action)

    async def _check_link_values(self, action: CorrectiveAction) -> None:
        if action.inspection_id is not None:
            inspection = await self.inspections.get(action.inspection_id)
            if inspection is None or inspection.factory_id != action.factory_id:
                raise InvalidDataError("Linked inspection does not belong to this factory")
        if action.incident_id is not None:
            incident = await self.incidents.get(action.incident_id)
            if incident is None or incident.factory_id != action.factory_id:
                raise InvalidDataError("Linked incident does not belong to this factory")

    @staticmethod
    def _sync_completed_at(action: CorrectiveAction) -> None:
        if action.status == ActionStatus.COMPLETED:
            action.completed_at = action.completed_at or now()
        else:
            action.completed_at = None
