from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import PageParams
from app.core.schemas import PatchModel
from app.modules.inspections.models import InspectionCategory, InspectionStatus


class InspectionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    factory_id: int
    inspector_id: int | None = None
    inspection_date: date
    category: InspectionCategory
    status: InspectionStatus = InspectionStatus.SCHEDULED
    score: int | None = Field(default=None, ge=0, le=100)
    findings: str | None = Field(default=None, max_length=5000)


class InspectionUpdate(PatchModel):
    nullable_fields = frozenset({"inspector_id", "score", "findings"})

    inspector_id: int | None = None
    inspection_date: date | None = None
    category: InspectionCategory | None = None
    status: InspectionStatus | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    findings: str | None = Field(default=None, max_length=5000)


class InspectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    factory_id: int
    inspector_id: int | None
    inspection_date: date
    category: InspectionCategory
    status: InspectionStatus
    score: int | None
    findings: str | None
    created_at: datetime
    updated_at: datetime


class InspectionFilters(PageParams):
    factory_id: int | None = None
    category: InspectionCategory | None = None
    status: InspectionStatus | None = None
    date_from: date | None = None
    date_to: date | None = None
