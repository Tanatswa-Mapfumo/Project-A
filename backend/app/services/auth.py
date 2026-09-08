"""Auth service: signup, login, refresh, forgot-password, logout."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth import supabase_client
from app.core.exceptions import AppError, ErrorCode
from app.core.security import create_mock_token, decode_mock_token, hash_password, verify_password
from app.repositories.profiles import ProfileRepository


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.profiles = ProfileRepository(session)

    async def signup(self, email: str, password: str) -> dict:
        if settings.auth_mode == "supabase":
            result = await supabase_client.signup(email, password)
            if result.get("requires_email_confirmation"):
                return result
            await self._ensure_profile(uuid.UUID(result["user"]["id"]), email)
            return result
        return await self._mock_signup(email, password)

    async def login(self, email: str, password: str) -> dict:
        if settings.auth_mode == "supabase":
            result = await supabase_client.login(email, password)
            await self._ensure_profile(uuid.UUID(result["user"]["id"]), email)
            return result
        return await self._mock_login(email, password)

    async def refresh(self, refresh_token: str) -> dict:
        if settings.auth_mode == "supabase":
            return await supabase_client.refresh(refresh_token)
        payload = decode_mock_token(refresh_token, "refresh")
        subject = payload["sub"]
        email = payload.get("email", "")
        await self._ensure_profile(uuid.UUID(subject), email)
        return self._mock_token_response(subject, email)

    async def forgot_password(self, email: str) -> None:
        if settings.auth_mode == "supabase":
            await supabase_client.recover_password(email)
        # Mock mode is stateless: nothing to do.

    async def logout(self, access_token: str) -> None:
        if settings.auth_mode == "supabase":
            await supabase_client.logout(access_token)
        # Mock mode is stateless: nothing to do.

    async def _mock_signup(self, email: str, password: str) -> dict:
        existing = await self.profiles.get_auth_user_by_email(email)
        if existing is not None:
            raise AppError(
                409,
                ErrorCode.AUTH_EMAIL_IN_USE,
                "An account with this email already exists.",
            )
        auth_user = await self.profiles.create_auth_user(email, hash_password(password))
        await self._ensure_profile(auth_user.id, email)
        await self.session.commit()
        return self._mock_token_response(str(auth_user.id), email)

    async def _mock_login(self, email: str, password: str) -> dict:
        auth_user = await self.profiles.get_auth_user_by_email(email)
        if auth_user is None or not auth_user.password_hash:
            raise AppError(401, ErrorCode.AUTH_INVALID_CREDENTIALS, "Invalid email or password.")
        if not verify_password(password, auth_user.password_hash):
            raise AppError(401, ErrorCode.AUTH_INVALID_CREDENTIALS, "Invalid email or password.")
        await self._ensure_profile(auth_user.id, email)
        return self._mock_token_response(str(auth_user.id), email)

    async def _ensure_profile(self, auth_user_id: uuid.UUID, email: str) -> None:
        profile = await self.profiles.get_by_auth_user_id(auth_user_id)
        if profile is None:
            await self.profiles.create(auth_user_id, email)

    @staticmethod
    def _mock_token_response(subject: str, email: str) -> dict:
        return {
            "access_token": create_mock_token("access", subject, email),
            "refresh_token": create_mock_token("refresh", subject, email),
            "expires_in": settings.access_token_expire_minutes * 60,
            "token_type": "bearer",
            "user": {"id": subject, "email": email},
        }
