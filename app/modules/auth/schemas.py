from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.auth.models import UserRole


def check_password(value: str) -> str:
    if not any(char.isalpha() for char in value) or not any(char.isdigit() for char in value):
        raise ValueError("Password must contain at least one letter and one number")
    return value


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()

    _password = field_validator("password")(check_password)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    role: UserRole
    is_active: bool
