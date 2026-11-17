from datetime import date, datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.core.pagination import PageParams
from app.core.schemas import Id, PatchModel
from app.modules.incidents.models import IncidentSeverity, IncidentStatus, IncidentType


class IncidentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    factory_id: Id
    occurred_at: AwareDatetime = Field(examples=["2026-11-10T10:40:00+06:00"])
    incident_type: IncidentType
    severity: IncidentSeverity
    location: str = Field(min_length=2, max_length=120, examples=["Cutting section, floor 2"])
    injured_count: int = Field(default=0, ge=0, le=1000)
    description: str = Field(min_length=10, max_length=5000)
    status: IncidentStatus = IncidentStatus.OPEN


class IncidentUpdate(PatchModel):
    occurred_at: AwareDatetime | None = None
    incident_type: IncidentType | None = None
    severity: IncidentSeverity | None = None
    location: str | None = Field(default=None, min_length=2, max_length=120)
    injured_count: int | None = Field(default=None, ge=0, le=1000)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    status: IncidentStatus | None = None


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    factory_id: int
    reported_by_id: int | None
    occurred_at: datetime
    incident_type: IncidentType
    severity: IncidentSeverity
    location: str
    injured_count: int
    description: str
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime


class IncidentFilters(PageParams):
    factory_id: Id | None = None
    incident_type: IncidentType | None = None
    severity: IncidentSeverity | None = None
    status: IncidentStatus | None = None
    search: str | None = Field(default=None, max_length=100, description="Description or location")
    date_from: date | None = None
    date_to: date | None = None
