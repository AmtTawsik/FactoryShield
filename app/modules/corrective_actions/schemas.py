from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.pagination import PageParams
from app.core.schemas import Id, PatchModel
from app.core.time import today
from app.modules.corrective_actions.models import ActionPriority, ActionStatus


class ActionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    factory_id: Id
    inspection_id: Id | None = None
    incident_id: Id | None = None
    title: str = Field(min_length=5, max_length=200, examples=["Refill expired extinguishers on floor 3"])
    description: str | None = Field(default=None, max_length=5000)
    priority: ActionPriority = ActionPriority.MEDIUM
    assigned_to: str = Field(min_length=2, max_length=120, examples=["Fire Safety Officer"])
    due_date: date
    status: ActionStatus = ActionStatus.OPEN


class ActionUpdate(PatchModel):
    nullable_fields = frozenset({"inspection_id", "incident_id", "description"})

    inspection_id: Id | None = None
    incident_id: Id | None = None
    title: str | None = Field(default=None, min_length=5, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    priority: ActionPriority | None = None
    assigned_to: str | None = Field(default=None, min_length=2, max_length=120)
    due_date: date | None = None
    status: ActionStatus | None = None


class ActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    factory_id: int
    inspection_id: int | None
    incident_id: int | None
    title: str
    description: str | None
    priority: ActionPriority
    assigned_to: str
    due_date: date
    status: ActionStatus
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_overdue(self) -> bool:
        return self.status != ActionStatus.COMPLETED and self.due_date < today()


class ActionFilters(PageParams):
    factory_id: Id | None = None
    status: ActionStatus | None = None
    priority: ActionPriority | None = None
    overdue: bool | None = None
    inspection_id: Id | None = None
    incident_id: Id | None = None
    search: str | None = Field(default=None, max_length=100, description="Title or assignee")
