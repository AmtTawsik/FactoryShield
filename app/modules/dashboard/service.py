from datetime import date

from app.core.time import today
from app.modules.auth.service import FactoryScope
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schemas import (
    ActionTotals,
    DashboardFilters,
    DashboardSummary,
    FactoryOverdue,
    IncidentTotals,
    InspectionTotals,
    MonthlyScore,
    SeverityCount,
    UpcomingInspection,
)
from app.modules.factories.service import FactoryService
from app.modules.incidents.models import IncidentSeverity

TREND_MONTHS = 6
TOP_LIMIT = 5


class DashboardService:
    def __init__(self, dashboard: DashboardRepository, factories: FactoryService):
        self.dashboard = dashboard
        self.factories = factories

    async def summary(self, filters: DashboardFilters, scope: FactoryScope) -> DashboardSummary:
        factory_ids = scope.factory_ids
        if filters.factory_id is not None:
            factory = await self.factories.get(filters.factory_id, scope)
            factory_ids = frozenset({factory.id})

        on_date = today()
        factories, workers = await self.dashboard.factory_totals(factory_ids)
        completed, average, upcoming = await self.dashboard.inspection_totals(factory_ids, on_date)
        not_closed, serious, recent = await self.dashboard.incident_totals(factory_ids, on_date)
        pending, overdue, done = await self.dashboard.action_totals(factory_ids, on_date)

        months = _last_months(on_date, TREND_MONTHS)
        scores = await self.dashboard.monthly_scores(factory_ids, date.fromisoformat(f"{months[0]}-01"), on_date)
        severities = await self.dashboard.incidents_by_severity(factory_ids, on_date)

        return DashboardSummary(
            as_of=on_date,
            factories=factories,
            workers=workers,
            inspections=InspectionTotals(
                completed_last_90_days=completed, average_score_last_90_days=average, scheduled_upcoming=upcoming
            ),
            incidents=IncidentTotals(not_closed=not_closed, serious_not_closed=serious, last_30_days=recent),
            actions=ActionTotals(not_completed=pending, overdue=overdue, completed_last_30_days=done),
            score_trend=[
                MonthlyScore(month=month, inspections=count, average_score=score)
                for month in months
                for count, score in [scores.get(month, (0, None))]
            ],
            incidents_by_severity=[
                SeverityCount(severity=severity, count=severities.get(severity, 0)) for severity in IncidentSeverity
            ],
            overdue_by_factory=[
                FactoryOverdue(factory_id=row[0], factory_name=row[1], overdue=row[2])
                for row in await self.dashboard.overdue_by_factory(factory_ids, on_date, TOP_LIMIT)
            ],
            upcoming_inspections=[
                UpcomingInspection(
                    id=row[0], factory_id=row[1], factory_name=row[2], inspection_date=row[3], category=row[4]
                )
                for row in await self.dashboard.upcoming_inspections(factory_ids, on_date, TOP_LIMIT)
            ],
        )


def _last_months(on_date: date, count: int) -> list[str]:
    year, month = on_date.year, on_date.month
    keys = []
    for _ in range(count):
        keys.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return keys[::-1]
