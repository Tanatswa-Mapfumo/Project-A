"""Auth endpoints (section 8)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, ErrorCode
from app.db.session import get_db
from app.schemas.auth import (
    EmailConfirmationRequiredResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageOut,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
_bearer = HTTPBearer(auto_error=False)

SIGNUP_EXAMPLE = {"email": "person@example.com", "password": "strong-password"}


@router.post(
    "/signup",
    response_model=TokenResponse | EmailConfirmationRequiredResponse,
    summary="Create an account",
    description="Creates a user with the auth provider and returns a session token pair. "
    "If the provider requires email confirmation, a `requires_email_confirmation` "
    "response is returned instead.",
    responses={409: {"description": "Email already in use."}},
)
async def signup(body: SignupRequest, session: DbSession):
    return await AuthService(session).signup(body.email, body.password)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in",
    description="Exchanges email and password for an access/refresh token pair.",
    responses={401: {"description": "Invalid credentials."}},
)
async def login(body: LoginRequest, session: DbSession):
    return await AuthService(session).login(body.email, body.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
    description="Exchanges a refresh token for a new access/refresh token pair.",
    responses={401: {"description": "Invalid or expired refresh token."}},
)
async def refresh(body: RefreshRequest, session: DbSession):
    return await AuthService(session).refresh(body.refresh_token)


@router.post(
    "/forgot-password",
    response_model=MessageOut,
    summary="Request password reset",
    description="Triggers the auth provider's password recovery flow for the given email.",
)
async def forgot_password(body: ForgotPasswordRequest, session: DbSession):
    await AuthService(session).forgot_password(body.email)
    return MessageOut(message="If the account exists, a recovery email has been sent.")


@router.post(
    "/logout",
    status_code=204,
    summary="Log out",
    description="Invalidates the current session with the auth provider where supported.",
)
async def logout(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
):
    if credentials is None:
        raise AppError(401, ErrorCode.AUTH_REQUIRED, "Authentication is required.")
    await AuthService(session).logout(credentials.credentials)
