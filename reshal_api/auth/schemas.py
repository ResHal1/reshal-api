import re
import uuid
from typing import Literal, Optional

from pydantic import EmailStr, Extra, validator

from reshal_api.base import ORJSONBaseModel

from .models import UserRole

# Validators
EMAIL_BLACKLIST_REGEX = re.compile(
    r"^(admin|administrator|root|sysadmin|me|sales|info|support|contact|help|feedback|abuse|webmaster|postmaster|noreply|marketing|spam)@reshal\.com$"
)
PASSWORD_REGEX = re.compile(r"^(?=.*[\d])(?=.*[!@#$%^&*()_+])[\w!@#$%^&*()_+]{6,128}$")


def validate_email_in_blacklist(email: str) -> str:
    if re.match(EMAIL_BLACKLIST_REGEX, email):
        raise ValueError("Email is not allowed")
    return email


def validate_password_complexity(password: str) -> str:
    if not re.match(PASSWORD_REGEX, password):
        raise ValueError(
            "Password must contain at least one digit"
            " and one special character from the set !@#$%^&*()_+"
            " and be between 6 and 128 characters long"
        )
    return password


# Schemas


class UserRead(ORJSONBaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole

    class Config:
        orm_mode = True


class UserCreate(ORJSONBaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str

    _validate_password_complexity = validator("password", allow_reuse=True)(
        validate_password_complexity
    )

    _validate_email_in_blacklist = validator("email", allow_reuse=True)(
        validate_email_in_blacklist
    )

    class Config:
        error_msg_templates = {"value_error.email": "Email address is not valid"}


class UserUpdate(ORJSONBaseModel):
    current_password: str
    new_password: Optional[str]
    email: Optional[EmailStr]
    first_name: Optional[str]
    last_name: Optional[str]
    last_name: Optional[str]

    _validate_password_complexity = validator("new_password", allow_reuse=True)(
        validate_password_complexity
    )

    _validate_email_in_blacklist = validator("email", allow_reuse=True)(
        validate_email_in_blacklist
    )

    class Config:
        error_msg_templates = {"value_error.email": "Email address is not valid"}


# JWT


class AuthRequest(ORJSONBaseModel):
    email: str
    password: str

    class Config:
        extra = Extra.allow


class JWTData(ORJSONBaseModel):
    user_id: uuid.UUID
    role: UserRole


class AccessTokenResponse(ORJSONBaseModel):
    access_token: str
    token_type: Literal["bearer"]
