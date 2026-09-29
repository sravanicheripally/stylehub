from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)
    phone: str | None = Field(
        default=None,
        max_length=20,
    )


class AdminUserCreate(UserRegister):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    role: UserRole

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value: str | UserRole) -> str | UserRole:
        if isinstance(value, str):
            return value.lower()
        return value


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    phone: str | None
    role: str
    is_active: bool

    model_config = {
        "from_attributes": True,
    }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"