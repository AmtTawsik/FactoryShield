from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, string_enum
from app.modules.auth.models import User
from app.modules.factories.models import Factory


class IncidentType(StrEnum):
    INJURY = "injury"
    FIRE = "fire"
    ELECTRICAL = "electrical"
    CHEMICAL = "chemical"
    STRUCTURAL = "structural"
    NEAR_MISS = "near_miss"


class IncidentSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CLOSED = "closed"


class SafetyIncident(TimestampMixin, Base):
    __tablename__ = "safety_incidents"
    __table_args__ = (CheckConstraint("injured_count >= 0", name="injured_count_not_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), index=True)
    reported_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    incident_type: Mapped[IncidentType] = mapped_column(string_enum(IncidentType, "incident_type"))
    severity: Mapped[IncidentSeverity] = mapped_column(string_enum(IncidentSeverity, "incident_severity"), index=True)
    location: Mapped[str] = mapped_column(String(120))
    injured_count: Mapped[int] = mapped_column(default=0, server_default="0")
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[IncidentStatus] = mapped_column(
        string_enum(IncidentStatus, "incident_status"), default=IncidentStatus.OPEN, index=True
    )

    factory: Mapped[Factory] = relationship()
    reported_by: Mapped[User | None] = relationship()
