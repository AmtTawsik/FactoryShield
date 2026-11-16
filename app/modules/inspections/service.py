from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import InvalidDataError, NotFoundError
from app.core.pagination import Page
from app.core.time import today
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import FactoryScope
from app.modules.factories.repository import FactoryRepository
from app.modules.inspections.models import InspectionStatus, SafetyInspection
from app.modules.inspections.repository import InspectionRepository
from app.modules.inspections.schemas import (
    InspectionCreate,
    InspectionFilters,
    InspectionResponse,
    InspectionUpdate,
)


class InspectionService:
    def __init__(
        self,
        session: AsyncSession,
        inspections: InspectionRepository,
        factories: FactoryRepository,
        users: UserRepository,
    ):
        self.session = session
        self.inspections = inspections
        self.factories = factories
        self.users = users

    async def list(self, filters: InspectionFilters, scope: FactoryScope) -> Page[InspectionResponse]:
        items, total = await self.inspections.list(filters, scope.factory_ids)
        return Page(
            items=[InspectionResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            size=filters.size,
        )

    async def get(self, inspection_id: int, scope: FactoryScope) -> SafetyInspection:
        inspection = await self.inspections.get(inspection_id)
        if inspection is None or not scope.allows(inspection.factory_id):
            raise NotFoundError("Safety inspection not found")
        return inspection

    async def create(self, data: InspectionCreate, scope: FactoryScope) -> SafetyInspection:
        if await self.factories.get(data.factory_id) is None or not scope.allows(data.factory_id):
            raise NotFoundError("Factory not found")
        await self._check_inspector(data.inspector_id)

        inspection = SafetyInspection(**data.model_dump())
        self._check_rules(inspection)
        self.inspections.add(inspection)
        await self.session.commit()
        await self.session.refresh(inspection)
        return inspection

    async def update(self, inspection_id: int, data: InspectionUpdate, scope: FactoryScope) -> SafetyInspection:
        inspection = await self.get(inspection_id, scope)
        changes = data.changes()
        if "inspector_id" in changes:
            await self._check_inspector(changes["inspector_id"])
        for field, value in changes.items():
            setattr(inspection, field, value)
        self._check_rules(inspection)
        await self.session.commit()
        await self.session.refresh(inspection)
        return inspection

    async def delete(self, inspection_id: int, scope: FactoryScope) -> None:
        inspection = await self.get(inspection_id, scope)
        await self.inspections.delete(inspection)
        await self.session.commit()

    async def _check_inspector(self, inspector_id: int | None) -> None:
        if inspector_id is None:
            return
        inspector = await self.users.get_by_id(inspector_id)
        if inspector is None or not inspector.is_active:
            raise InvalidDataError("Inspector must be an active user")

    @staticmethod
    def _check_rules(inspection: SafetyInspection) -> None:
        if inspection.status == InspectionStatus.COMPLETED:
            if inspection.score is None:
                raise InvalidDataError("A completed inspection needs a score")
            if inspection.inspection_date > today():
                raise InvalidDataError("An inspection cannot be completed with a future date")
        elif inspection.score is not None:
            raise InvalidDataError("A scheduled inspection cannot have a score yet")
