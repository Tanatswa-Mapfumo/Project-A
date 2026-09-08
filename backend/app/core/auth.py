"""Authentication: Supabase Auth client, mock auth, and the current-user dependency.

AUTH_MODE=supabase: identity and tokens are managed by Supabase Auth. Access tokens are
verified locally against Supabase's published JWKS (cached).
AUTH_MODE=mock: for local dev/tests only. Passwords are stored as PBKDF2 hashes in the
local `auth_users` table (never raw); JWTs are signed with a dev secret.
"""

import time
import uuid
from dataclasses import dataclass
from typing import Annotated, Any

import httpx
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AppError, ErrorCode
from app.core.security import decode_mock_token
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    profile_id: str  # profiles.id
    auth_user_id: str  # auth provider user id
    email: str


class SupabaseClient:
    """Thin async adapter over the Supabase Auth REST API."""

    def __init__(self) -> None:
        self._jwks: dict[str, Any] | None = None
        self._jwks_fetched_at: float = 0.0
        self._jwks_ttl = 3600.0

    def _headers(self, anon: bool = True) -> dict[str, str]:
        key = settings.supabase_anon_key if anon else settings.supabase_service_role_key
        return {"apikey": key, "Authorization": f"Bearer {key}"}

    async def _post(self, path: str, payload: dict[str, Any], anon: bool = True) -> dict[str, Any]:
        if not settings.supabase_url:
            raise AppError(503, ErrorCode.DEPENDENCY_UNAVAILABLE, "Supabase is not configured.")
        url = f"{settings.supabase_url.rstrip('/')}{path}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=self._headers(anon))
        except httpx.HTTPError as exc:
            raise AppError(
                503, ErrorCode.DEPENDENCY_UNAVAILABLE, "Supabase is unreachable."
            ) from exc
        return resp.json()

    async def signup(self, email: str, password: str) -> dict[str, Any]:
        data = await self._post(
            "/auth/v1/signup",
            {"email": email, "password": password, "data": {}},
        )
        if "error" in data or (settings.auth_require_email_confirm and not data.get("session")):
            return {"requires_email_confirmation": True}
        session = data.get("session") or {}
        user = data.get("user") or {}
        return self._token_payload(session, user)

    async def login(self, email: str, password: str) -> dict[str, Any]:
        data = await self._post(
            "/auth/v1/token?grant_type=password",
            {"email": email, "password": password},
        )
        if "error" in data or not data.get("access_token"):
            raise AppError(401, ErrorCode.AUTH_INVALID_CREDENTIALS, "Invalid email or password.")
        return self._token_payload(data, {"id": data.get("user", {}).get("id"), "email": email})

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        data = await self._post(
            "/auth/v1/token?grant_type=refresh_token",
            {"refresh_token": refresh_token},
        )
        if "error" in data or not data.get("access_token"):
            raise AppError(401, ErrorCode.AUTH_INVALID, "The refresh token is invalid.")
        return self._token_payload(data, {"id": data.get("user", {}).get("id")})

    async def recover_password(self, email: str) -> None:
        await self._post("/auth/v1/recover", {"email": email})

    async def logout(self, access_token: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"{settings.supabase_url.rstrip('/')}/auth/v1/logout",
                    headers={
                        "apikey": settings.supabase_anon_key,
                        "Authorization": f"Bearer {access_token}",
                    },
                )
        except httpx.HTTPError as exc:
            raise AppError(
                503, ErrorCode.DEPENDENCY_UNAVAILABLE, "Supabase is unreachable."
            ) from exc

    @staticmethod
    def _token_payload(session: dict[str, Any], user: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "access_token": session.get("access_token", ""),
            "refresh_token": session.get("refresh_token", ""),
            "expires_in": session.get("expires_in", 3600),
            "token_type": "bearer",
            "user": {
                "id": (user or {}).get("id") or session.get("user", {}).get("id", ""),
                "email": (user or {}).get("email") or session.get("user", {}).get("email", ""),
            },
        }

    async def verify_access_token(self, token: str) -> CurrentUser:
        """Locally verify a Supabase-issued JWT using the cached JWKS."""
        if not settings.supabase_url:
            raise AppError(503, ErrorCode.DEPENDENCY_UNAVAILABLE, "Supabase is not configured.")
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        jwks = await self._get_jwks()
        key_data = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if key_data is None:
            await self._refresh_jwks()
            jwks = await self._get_jwks()
            key_data = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if key_data is None:
            raise AppError(401, ErrorCode.AUTH_INVALID, "The access token is invalid.")
        try:
            from jwt import PyJWK

            jwk = PyJWK.from_dict(key_data)
            payload = jwt.decode(
                token,
                jwk.key,
                algorithms=["RS256"],
                audience="authenticated",
                options={"verify_aud": True},
            )
        except jwt.ExpiredSignatureError as exc:
            raise AppError(401, ErrorCode.AUTH_EXPIRED, "The access token has expired.") from exc
        except jwt.InvalidTokenError as exc:
            raise AppError(401, ErrorCode.AUTH_INVALID, "The access token is invalid.") from exc
        return CurrentUser(
            profile_id="", auth_user_id=payload.get("sub", ""), email=payload.get("email", "")
        )

    async def _get_jwks(self) -> dict[str, Any]:
        if self._jwks is None:
            await self._refresh_jwks()
        return self._jwks or {}

    async def _refresh_jwks(self) -> None:
        if time.monotonic() - self._jwks_fetched_at < self._jwks_ttl and self._jwks is not None:
            return
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{settings.supabase_url.rstrip('/')}/auth/v1/keys")
                resp.raise_for_status()
                self._jwks = resp.json()
                self._jwks_fetched_at = time.monotonic()
        except httpx.HTTPError as exc:
            raise AppError(
                503, ErrorCode.DEPENDENCY_UNAVAILABLE, "Supabase is unreachable."
            ) from exc


supabase_client = SupabaseClient()


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CurrentUser:
    """Parse the Bearer token, validate it, and resolve the local profile.

    Never trusts a client-provided user id. If no profile row exists yet (e.g. the
    user signed up directly in Supabase), one is created lazily.
    """
    if credentials is None:
        raise AppError(401, ErrorCode.AUTH_REQUIRED, "Authentication is required.")
    token = credentials.credentials

    if settings.auth_mode == "supabase":
        user = await supabase_client.verify_access_token(token)
    else:
        payload = decode_mock_token(token, "access")
        user = CurrentUser(
            profile_id="",
            auth_user_id=payload.get("sub", ""),
            email=payload.get("email", ""),
        )
    if not user.auth_user_id:
        raise AppError(401, ErrorCode.AUTH_INVALID, "The access token is invalid.")

    from app.repositories.profiles import ProfileRepository

    repo = ProfileRepository(session)
    try:
        auth_id = uuid.UUID(user.auth_user_id)
    except ValueError as exc:
        raise AppError(401, ErrorCode.AUTH_INVALID, "The access token is invalid.") from exc
    profile = await repo.get_by_auth_user_id(auth_id)
    if profile is None:
        profile = await repo.create(auth_id, user.email)
        await session.commit()
    request.state.user_id = str(profile.id)
    request.state.tz_name = profile.timezone or settings.default_timezone
    return CurrentUser(profile_id=str(profile.id), auth_user_id=str(auth_id), email=profile.email)
