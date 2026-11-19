from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, string_enum
from app.modules.organizations.models import Organization


class UserRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    STAFF = "staff"


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        CheckConstraint("(role = 'super_admin') = (organization_id IS NULL)", name="organization_matches_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        string_enum(UserRole, "user_role"), default=UserRole.STAFF, server_default=UserRole.STAFF.value
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), index=True)

    organization: Mapped[Organization | None] = relationship(lazy="joined")
