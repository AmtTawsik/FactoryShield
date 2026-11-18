from sqlalchemy import Index, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class Organization(TimestampMixin, Base):
    """A customer company (tenant). Its factories, users and private documents belong only to it."""

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    # An inactive organization's users cannot sign in, and their existing tokens stop working.
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())


# Names are unique regardless of letter case.
Index("uq_organizations_name_lower", func.lower(Organization.name), unique=True)
