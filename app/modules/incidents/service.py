from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InvalidDataError, NotFoundError
from app.core.pagination import Page
from app.core.time import now
from app.modules.auth.models import User
from app.modules.auth.service import FactoryScope
from app.modules.factories.repository import FactoryRepository
from app.modules.incidents.models import SafetyIncident
from app.modules.incidents.repository import IncidentRepository
from app.modules.incidents.schemas import IncidentCreate, IncidentFilters, IncidentResponse, IncidentUpdate


class IncidentService:
    def __init__(self, session: AsyncSession, incidents: IncidentRepository, factories: FactoryRepository):
        self.session = session
        self.incidents = incidents
        self.factories = factories

    async def list(self, filters: IncidentFilters, scope: FactoryScope) -> Page[IncidentResponse]:
        items, total = await self.incidents.list(filters, scope.factory_ids)
        return Page(
            items=[IncidentResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            size=filters.size,
        )

    async def get(self, incident_id: int, scope: FactoryScope) -> SafetyIncident:
        incident = await self.incidents.get(incident_id)
        if incident is None or not scope.allows(incident.factory_id):
            raise NotFoundError("Safety incident not found")
        return incident

    async def create(self, data: IncidentCreate, reporter: User, scope: FactoryScope) -> SafetyIncident:
        if await self.factories.get(data.factory_id) is None or not scope.allows(data.factory_id):
            raise NotFoundError("Factory not found")

        incident = SafetyIncident(**data.model_dump(), reported_by_id=reporter.id)
        self._check_rules(incident)
        self.incidents.add(incident)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def update(self, incident_id: int, data: IncidentUpdate, scope: FactoryScope) -> SafetyIncident:
        incident = await self.get(incident_id, scope)
        for field, value in data.changes().items():
            setattr(incident, field, value)
        self._check_rules(incident)
        await self.session.commit()
        await self.session.refresh(incident)
        return incident

    async def delete(self, incident_id: int, scope: FactoryScope) -> None:
        incident = await self.get(incident_id, scope)
        await self.incidents.delete(incident)
        await self.session.commit()

    @staticmethod
    def _check_rules(incident: SafetyIncident) -> None:
        if incident.occurred_at > now():
            raise InvalidDataError("Incident time cannot be in the future")
