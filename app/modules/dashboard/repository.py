from datetime import date, datetime, time, timedelta

from sqlalchemy import ColumnElement, and_, func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import DHAKA_TZ
from app.modules.corrective_actions.models import ActionStatus, CorrectiveAction
from app.modules.corrective_actions.repository import overdue_condition
from app.modules.factories.models import Factory
from app.modules.incidents.models import IncidentSeverity, IncidentStatus, SafetyIncident
from app.modules.inspections.models import InspectionStatus, SafetyInspection

SERIOUS = (IncidentSeverity.HIGH, IncidentSeverity.CRITICAL)


def _in_scope(column, factory_ids: frozenset[int] | None) -> ColumnElement[bool]:
    return true() if factory_ids is None else column.in_(factory_ids)


def _start_of(day: date) -> datetime:
    return datetime.combine(day, time(), DHAKA_TZ)


class DashboardRepository:
    """Aggregate queries only. `factory_ids` is the set to cover; `None` means every factory."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def factory_totals(self, factory_ids: frozenset[int] | None) -> tuple[int, int]:
        row = (
            await self.session.execute(
                select(func.count(), func.coalesce(func.sum(Factory.worker_count), 0)).where(
                    Factory.is_active, _in_scope(Factory.id, factory_ids)
                )
            )
        ).one()
        return row[0], row[1]

    async def inspection_totals(
        self, factory_ids: frozenset[int] | None, on_date: date
    ) -> tuple[int, float | None, int]:
        scope = _in_scope(SafetyInspection.factory_id, factory_ids)
        completed = and_(
            scope,
            SafetyInspection.status == InspectionStatus.COMPLETED,
            SafetyInspection.inspection_date > on_date - timedelta(days=90),
            SafetyInspection.inspection_date <= on_date,
        )
        count, average = (
            await self.session.execute(
                select(func.count(), func.round(func.avg(SafetyInspection.score), 1)).where(completed)
            )
        ).one()
        upcoming = await self.session.scalar(
            select(func.count()).where(
                scope, SafetyInspection.status == InspectionStatus.SCHEDULED, SafetyInspection.inspection_date >= on_date
            )
        )
        return count, (float(average) if average is not None else None), upcoming

    async def incident_totals(self, factory_ids: frozenset[int] | None, on_date: date) -> tuple[int, int, int]:
        scope = _in_scope(SafetyIncident.factory_id, factory_ids)
        not_closed = SafetyIncident.status != IncidentStatus.CLOSED
        row = (
            await self.session.execute(
                select(
                    func.count().filter(not_closed),
                    func.count().filter(not_closed, SafetyIncident.severity.in_(SERIOUS)),
                    func.count().filter(SafetyIncident.occurred_at >= _start_of(on_date - timedelta(days=29))),
                ).where(scope)
            )
        ).one()
        return row[0], row[1], row[2]

    async def action_totals(self, factory_ids: frozenset[int] | None, on_date: date) -> tuple[int, int, int]:
        row = (
            await self.session.execute(
                select(
                    func.count().filter(CorrectiveAction.status != ActionStatus.COMPLETED),
                    func.count().filter(overdue_condition(on_date)),
                    func.count().filter(
                        CorrectiveAction.status == ActionStatus.COMPLETED,
                        CorrectiveAction.completed_at >= _start_of(on_date - timedelta(days=29)),
                    ),
                ).where(_in_scope(CorrectiveAction.factory_id, factory_ids))
            )
        ).one()
        return row[0], row[1], row[2]

    async def monthly_scores(
        self, factory_ids: frozenset[int] | None, since: date, until: date
    ) -> dict[str, tuple[int, float | None]]:
        month = func.to_char(SafetyInspection.inspection_date, "YYYY-MM")
        rows = await self.session.execute(
            select(month, func.count(), func.round(func.avg(SafetyInspection.score), 1))
            .where(
                _in_scope(SafetyInspection.factory_id, factory_ids),
                SafetyInspection.status == InspectionStatus.COMPLETED,
                SafetyInspection.inspection_date >= since,
                SafetyInspection.inspection_date <= until,
            )
            .group_by(month)
        )
        return {key: (count, float(average) if average is not None else None) for key, count, average in rows}

    async def incidents_by_severity(
        self, factory_ids: frozenset[int] | None, on_date: date
    ) -> dict[IncidentSeverity, int]:
        rows = await self.session.execute(
            select(SafetyIncident.severity, func.count())
            .where(
                _in_scope(SafetyIncident.factory_id, factory_ids),
                SafetyIncident.occurred_at >= _start_of(on_date - timedelta(days=89)),
            )
            .group_by(SafetyIncident.severity)
        )
        return {severity: count for severity, count in rows}

    async def overdue_by_factory(self, factory_ids: frozenset[int] | None, on_date: date, limit: int) -> list:
        overdue = func.count().label("overdue")
        return list(
            await self.session.execute(
                select(Factory.id, Factory.name, overdue)
                .join(CorrectiveAction, CorrectiveAction.factory_id == Factory.id)
                .where(_in_scope(Factory.id, factory_ids), overdue_condition(on_date))
                .group_by(Factory.id, Factory.name)
                .order_by(overdue.desc(), Factory.name)
                .limit(limit)
            )
        )

    async def upcoming_inspections(self, factory_ids: frozenset[int] | None, on_date: date, limit: int) -> list:
        return list(
            await self.session.execute(
                select(
                    SafetyInspection.id,
                    SafetyInspection.factory_id,
                    Factory.name,
                    SafetyInspection.inspection_date,
                    SafetyInspection.category,
                )
                .join(Factory, Factory.id == SafetyInspection.factory_id)
                .where(
                    _in_scope(SafetyInspection.factory_id, factory_ids),
                    SafetyInspection.status == InspectionStatus.SCHEDULED,
                    SafetyInspection.inspection_date >= on_date,
                )
                .order_by(SafetyInspection.inspection_date, SafetyInspection.id)
                .limit(limit)
            )
        )
