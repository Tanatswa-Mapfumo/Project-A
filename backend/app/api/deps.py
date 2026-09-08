"""Shared API dependencies."""

from typing import Annotated

from fastapi import Depends, Request

from app.config import settings


def get_tz(request: Request) -> str:
    return getattr(request.state, "tz_name", None) or settings.default_timezone


TzName = Annotated[str, Depends(get_tz)]


def rate_limit(key: str, per_minute: int):
    from typing import Annotated as _A

    from fastapi import Depends as _D

    from app.core.auth import CurrentUser, get_current_user
    from app.core.exceptions import AppError, ErrorCode
    from app.core.ratelimit import limiter

    async def dependency(
        request: Request,
        user: _A[CurrentUser, _D(get_current_user)],
    ) -> None:
        if not limiter.allow(f"{key}:{user.profile_id}", per_minute):
            raise AppError(
                429, ErrorCode.RATE_LIMITED, "Too many requests. Please try again shortly."
            )

    return dependency
