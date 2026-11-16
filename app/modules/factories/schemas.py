import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.pagination import PageParams
from app.core.schemas import PatchModel

LICENSE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9/-]{2,49}$")
BD_MOBILE_PATTERN = re.compile(r"^(?:\+?880|0)?(1[3-9]\d{8})$")


def normalize_license(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip().upper()
    if not LICENSE_PATTERN.match(value):
        raise ValueError("Licence number may only contain letters, numbers, '-' and '/'")
    return value


def normalize_phone(value: str | None) -> str | None:
    if value is None:
        return None
    match = BD_MOBILE_PATTERN.match(re.sub(r"[\s-]", "", value))
    if not match:
        raise ValueError("Enter a valid Bangladeshi mobile number, e.g. 01711-234567")
    return f"+880{match.group(1)}"


class FactoryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=150, examples=["Sonali Thread Knit Composite Ltd"])
    license_number: str = Field(max_length=50, examples=["FL-GZP-04512"])
    address: str = Field(min_length=5, max_length=255, examples=["Plot 14, Konabari BSCIC Industrial Area"])
    district: str = Field(min_length=2, max_length=50, examples=["Gazipur"])
    worker_count: int = Field(gt=0, le=100_000, examples=[1450])
    floor_count: int = Field(gt=0, le=50, examples=[6])
    contact_person: str = Field(min_length=2, max_length=120, examples=["Kamrul Islam"])
    contact_phone: str = Field(max_length=20, examples=["01711-234567"])

    _license = field_validator("license_number")(normalize_license)
    _phone = field_validator("contact_phone")(normalize_phone)


class FactoryUpdate(PatchModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    license_number: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, min_length=5, max_length=255)
    district: str | None = Field(default=None, min_length=2, max_length=50)
    worker_count: int | None = Field(default=None, gt=0, le=100_000)
    floor_count: int | None = Field(default=None, gt=0, le=50)
    contact_person: str | None = Field(default=None, min_length=2, max_length=120)
    contact_phone: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None

    _license = field_validator("license_number")(normalize_license)
    _phone = field_validator("contact_phone")(normalize_phone)


class FactoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    license_number: str
    address: str
    district: str
    worker_count: int
    floor_count: int
    contact_person: str
    contact_phone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FactoryFilters(PageParams):
    search: str | None = Field(default=None, max_length=100, description="Name or licence number")
    district: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None
