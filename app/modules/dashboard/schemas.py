from datetime import date

from pydantic import BaseModel, Field

from app.core.schemas import Id
from app.modules.incidents.models import IncidentSeverity
from app.modules.inspections.models import InspectionCategory


class DashboardFilters(BaseModel):
    factory_id: Id | None = Field(default=None, description="Limit the summary to one factory")


class InspectionTotals(BaseModel):
    completed_last_90_days: int
    average_score_last_90_days: float | None
    scheduled_upcoming: int


class IncidentTotals(BaseModel):
    not_closed: int
    serious_not_closed: int = Field(description="High or critical incidents that are not closed")
    last_30_days: int


class ActionTotals(BaseModel):
    not_completed: int
    overdue: int
    completed_last_30_days: int


class MonthlyScore(BaseModel):
    month: str = Field(examples=["2026-11"])
    inspections: int
    average_score: float | None


class SeverityCount(BaseModel):
    severity: IncidentSeverity
    count: int


class FactoryOverdue(BaseModel):
    factory_id: int
    factory_name: str
    overdue: int


class UpcomingInspection(BaseModel):
    id: int
    factory_id: int
    factory_name: str
    inspection_date: date
    category: InspectionCategory


class DashboardSummary(BaseModel):
    as_of: date
    factories: int = Field(description="Active factories")
    workers: int = Field(description="Workers in active factories")
    inspections: InspectionTotals
    incidents: IncidentTotals
    actions: ActionTotals
    score_trend: list[MonthlyScore] = Field(description="Completed inspections per month, last 6 months, oldest first")
    incidents_by_severity: list[SeverityCount] = Field(description="Incidents in the last 90 days")
    overdue_by_factory: list[FactoryOverdue] = Field(description="Factories with the most overdue actions (top 5)")
    upcoming_inspections: list[UpcomingInspection] = Field(description="Next 5 scheduled inspections")
