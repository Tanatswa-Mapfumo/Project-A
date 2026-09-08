"""Auth schemas."""

import uuid

from pydantic import EmailStr, Field

from app.schemas.common import APIModel


class SignupRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(APIModel):
    refresh_token: str = Field(min_length=1)


class ForgotPasswordRequest(APIModel):
    email: EmailStr


class UserSummary(APIModel):
    id: uuid.UUID
    email: str


class TokenResponse(APIModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"
    user: UserSummary


class EmailConfirmationRequiredResponse(APIModel):
    requires_email_confirmation: bool = True


class MessageOut(APIModel):
    message: str
