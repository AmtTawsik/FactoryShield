from enum import StrEnum

from sqlalchemy import CheckConstraint, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, string_enum


class UserRole(StrEnum):
    ADMIN = "admin"
    STAFF = "staff"


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("email = lower(email)", name="email_lowercase"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        string_enum(UserRole, "user_role"), default=UserRole.STAFF, server_default=UserRole.STAFF.value
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
