from datetime import datetime, time, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate
from app.core.time import DHAKA_TZ
from app.modules.incidents.models import SafetyIncident
from app.modules.incidents.schemas import IncidentFilters


class IncidentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, incident_id: int) -> SafetyIncident | None:
        return await self.session.get(SafetyIncident, incident_id)

    async def list(
        self, filters: IncidentFilters, factory_ids: frozenset[int] | None
    ) -> tuple[list[SafetyIncident], int]:
        query = select(SafetyIncident)
        if factory_ids is not None:
            query = query.where(SafetyIncident.factory_id.in_(factory_ids))
        if filters.factory_id is not None:
            query = query.where(SafetyIncident.factory_id == filters.factory_id)
        if filters.incident_type:
            query = query.where(SafetyIncident.incident_type == filters.incident_type)
        if filters.severity:
            query = query.where(SafetyIncident.severity == filters.severity)
        if filters.status:
            query = query.where(SafetyIncident.status == filters.status)
        if filters.search:
            query = query.where(
                or_(
                    SafetyIncident.description.icontains(filters.search, autoescape=True),
                    SafetyIncident.location.icontains(filters.search, autoescape=True),
                )
            )
        # Dates are interpreted as Bangladesh calendar days.
        if filters.date_from:
            query = query.where(SafetyIncident.occurred_at >= datetime.combine(filters.date_from, time(), DHAKA_TZ))
        if filters.date_to:
            next_day = datetime.combine(filters.date_to + timedelta(days=1), time(), DHAKA_TZ)
            query = query.where(SafetyIncident.occurred_at < next_day)

        query = query.order_by(SafetyIncident.occurred_at.desc(), SafetyIncident.id.desc())
        return await paginate(self.session, query, filters)

    def add(self, incident: SafetyIncident) -> None:
        self.session.add(incident)

    async def delete(self, incident: SafetyIncident) -> None:
        await self.session.delete(incident)
