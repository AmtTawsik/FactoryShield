from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, string_enum
from app.modules.factories.models import Factory
from app.modules.incidents.models import SafetyIncident
from app.modules.inspections.models import SafetyInspection


class ActionPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CorrectiveAction(TimestampMixin, Base):
    __tablename__ = "corrective_actions"
    __table_args__ = (
        CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)", name="completed_at_matches_status"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), index=True)
    inspection_id: Mapped[int | None] = mapped_column(
        ForeignKey("safety_inspections.id", ondelete="SET NULL"), index=True
    )
    incident_id: Mapped[int | None] = mapped_column(
        ForeignKey("safety_incidents.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[ActionPriority] = mapped_column(
        string_enum(ActionPriority, "action_priority"), default=ActionPriority.MEDIUM
    )
    assigned_to: Mapped[str] = mapped_column(String(120))
    due_date: Mapped[date] = mapped_column(index=True)
    status: Mapped[ActionStatus] = mapped_column(
        string_enum(ActionStatus, "action_status"), default=ActionStatus.OPEN, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    factory: Mapped[Factory] = relationship()
    inspection: Mapped[SafetyInspection | None] = relationship()
    incident: Mapped[SafetyIncident | None] = relationship()
