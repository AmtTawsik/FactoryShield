from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.pagination import PageParams
from app.core.schemas import Id, PatchModel
from app.modules.auth.models import UserRole
from app.modules.auth.schemas import check_password

MAX_FACTORIES = 500


def unique_ids(value: list[int]) -> list[int]:
    return sorted(set(value))


def organization_role(value: UserRole | None) -> UserRole | None:
    if value == UserRole.SUPER_ADMIN:
        raise ValueError("Role must be admin or staff")
    return value


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.STAFF
    factory_ids: list[Id] = Field(
        default_factory=list, max_length=MAX_FACTORIES, description="Factories a staff user may access"
    )

    _password = field_validator("password")(check_password)
    _factories = field_validator("factory_ids")(unique_ids)
    _role = field_validator("role")(organization_role)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()


class UserUpdate(PatchModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128, description="Set a new password")

    _role = field_validator("role")(organization_role)

    @field_validator("password")
    @classmethod
    def password_rule(cls, value: str | None) -> str | None:
        return None if value is None else check_password(value)


class UserFactoriesUpdate(BaseModel):
    factory_ids: list[Id] = Field(max_length=MAX_FACTORIES, description="Replaces the user's factory list")

    _factories = field_validator("factory_ids")(unique_ids)


class UserDetail(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    factory_ids: list[int] = Field(description="Assigned factories (admins see every factory regardless)")
    created_at: datetime
    updated_at: datetime


class UserFilters(PageParams):
    search: str | None = Field(default=None, max_length=100, description="Name or email")
    role: UserRole | None = None
    is_active: bool | None = None
