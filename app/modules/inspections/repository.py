from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate
from app.modules.inspections.models import SafetyInspection
from app.modules.inspections.schemas import InspectionFilters


class InspectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, inspection_id: int) -> SafetyInspection | None:
        return await self.session.get(SafetyInspection, inspection_id)

    async def list(
        self, filters: InspectionFilters, factory_ids: frozenset[int] | None
    ) -> tuple[list[SafetyInspection], int]:
        query = select(SafetyInspection)
        if factory_ids is not None:
            query = query.where(SafetyInspection.factory_id.in_(factory_ids))
        if filters.factory_id is not None:
            query = query.where(SafetyInspection.factory_id == filters.factory_id)
        if filters.category:
            query = query.where(SafetyInspection.category == filters.category)
        if filters.status:
            query = query.where(SafetyInspection.status == filters.status)
        if filters.date_from:
            query = query.where(SafetyInspection.inspection_date >= filters.date_from)
        if filters.date_to:
            query = query.where(SafetyInspection.inspection_date <= filters.date_to)

        query = query.order_by(SafetyInspection.inspection_date.desc(), SafetyInspection.id.desc())
        return await paginate(self.session, query, filters)

    def add(self, inspection: SafetyInspection) -> None:
        self.session.add(inspection)

    async def delete(self, inspection: SafetyInspection) -> None:
        await self.session.delete(inspection)
