from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, CreatedAtMixin, TimestampMixin
from app.modules.auth.models import User


class Factory(TimestampMixin, Base):
    __tablename__ = "factories"
    __table_args__ = (
        CheckConstraint("worker_count > 0", name="worker_count_positive"),
        CheckConstraint("floor_count > 0", name="floor_count_positive"),
        UniqueConstraint("organization_id", "license_number", name="uq_factories_organization_id_license_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    license_number: Mapped[str] = mapped_column(String(50))
    address: Mapped[str] = mapped_column(String(255))
    district: Mapped[str] = mapped_column(String(50), index=True)
    worker_count: Mapped[int]
    floor_count: Mapped[int]
    contact_person: Mapped[str] = mapped_column(String(120))
    contact_phone: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())


class FactoryMembership(CreatedAtMixin, Base):

    __tablename__ = "factory_memberships"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    factory_id: Mapped[int] = mapped_column(
        ForeignKey("factories.id", ondelete="CASCADE"), primary_key=True, index=True
    )

    user: Mapped[User] = relationship()
    factory: Mapped[Factory] = relationship()
