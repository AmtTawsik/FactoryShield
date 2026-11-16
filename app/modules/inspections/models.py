from datetime import date
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, string_enum
from app.modules.auth.models import User
from app.modules.factories.models import Factory


class InspectionCategory(StrEnum):
    FIRE = "fire"
    ELECTRICAL = "electrical"
    STRUCTURAL = "structural"
    CHEMICAL = "chemical"
    PPE = "ppe"
    GENERAL = "general"


class InspectionStatus(StrEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"


class SafetyInspection(TimestampMixin, Base):
    __tablename__ = "safety_inspections"
    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),
        CheckConstraint("status = 'scheduled' OR score IS NOT NULL", name="completed_has_score"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), index=True)
    inspector_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    inspection_date: Mapped[date] = mapped_column(index=True)
    category: Mapped[InspectionCategory] = mapped_column(string_enum(InspectionCategory, "inspection_category"))
    status: Mapped[InspectionStatus] = mapped_column(
        string_enum(InspectionStatus, "inspection_status"), default=InspectionStatus.SCHEDULED, index=True
    )
    score: Mapped[int | None]
    findings: Mapped[str | None] = mapped_column(Text)

    factory: Mapped[Factory] = relationship()
    inspector: Mapped[User | None] = relationship()
