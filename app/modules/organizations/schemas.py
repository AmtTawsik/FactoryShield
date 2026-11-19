from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.pagination import PageParams
from app.core.schemas import PatchModel
from app.modules.auth.schemas import check_password


class AdminAccountCreate(BaseModel):

    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)

    _password = field_validator("password")(check_password)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=150, examples=["Rupali Apparel Group"])
    admin: AdminAccountCreate = Field(description="First admin of the new organization")


class OrganizationUpdate(PatchModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    is_active: bool | None = Field(default=None, description="Inactive organizations cannot sign in")


class OrganizationAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    is_active: bool


class OrganizationItem(BaseModel):
    id: int
    name: str
    is_active: bool
    user_count: int
    factory_count: int
    created_at: datetime
    updated_at: datetime


class OrganizationDetail(OrganizationItem):
    admins: list[OrganizationAdmin]


class OrganizationFilters(PageParams):
    search: str | None = Field(default=None, max_length=100, description="Organization name")
    is_active: bool | None = None
