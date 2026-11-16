from datetime import date

from sqlalchemy import ColumnElement, and_, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate
from app.modules.corrective_actions.models import ActionStatus, CorrectiveAction
from app.modules.corrective_actions.schemas import ActionFilters


def overdue_condition(on_date: date) -> ColumnElement[bool]:
    return and_(CorrectiveAction.status != ActionStatus.COMPLETED, CorrectiveAction.due_date < on_date)


class ActionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, action_id: int) -> CorrectiveAction | None:
        return await self.session.get(CorrectiveAction, action_id)

    async def list(
        self, filters: ActionFilters, factory_ids: frozenset[int] | None, on_date: date
    ) -> tuple[list[CorrectiveAction], int]:
        query = select(CorrectiveAction)
        if factory_ids is not None:
            query = query.where(CorrectiveAction.factory_id.in_(factory_ids))
        if filters.factory_id is not None:
            query = query.where(CorrectiveAction.factory_id == filters.factory_id)
        if filters.status:
            query = query.where(CorrectiveAction.status == filters.status)
        if filters.priority:
            query = query.where(CorrectiveAction.priority == filters.priority)
        if filters.overdue is True:
            query = query.where(overdue_condition(on_date))
        elif filters.overdue is False:
            query = query.where(not_(overdue_condition(on_date)))
        if filters.inspection_id is not None:
            query = query.where(CorrectiveAction.inspection_id == filters.inspection_id)
        if filters.incident_id is not None:
            query = query.where(CorrectiveAction.incident_id == filters.incident_id)
        if filters.search:
            query = query.where(
                or_(
                    CorrectiveAction.title.icontains(filters.search, autoescape=True),
                    CorrectiveAction.assigned_to.icontains(filters.search, autoescape=True),
                )
            )

        query = query.order_by(CorrectiveAction.due_date, CorrectiveAction.id)
        return await paginate(self.session, query, filters)

    def add(self, action: CorrectiveAction) -> None:
        self.session.add(action)

    async def delete(self, action: CorrectiveAction) -> None:
        await self.session.delete(action)
