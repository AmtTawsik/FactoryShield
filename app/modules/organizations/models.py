from sqlalchemy import Index, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class Organization(TimestampMixin, Base):

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())


Index("uq_organizations_name_lower", func.lower(Organization.name), unique=True)
