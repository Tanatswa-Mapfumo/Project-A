"""System endpoints: health and version."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.schemas.common import HealthOut, VersionOut

router = APIRouter(tags=["System"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get(
    "/health",
    response_model=HealthOut,
    summary="Health check",
    description="Verifies the API and its database dependency. Returns 503 when the "
    "database is unreachable.",
    responses={503: {"description": "Dependency unavailable."}},
)
async def health(session: DbSession):
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "DEPENDENCY_UNAVAILABLE",
                    "message": "The database is unreachable.",
                    "details": {},
                }
            },
        )
    return HealthOut(status="ok", service=settings.app_name, version=settings.app_version)


@router.get(
    "/version",
    response_model=VersionOut,
    summary="API and generator version",
    description="Returns the API version, the workout generator version, and the environment.",
)
async def version():
    return VersionOut(
        version=settings.app_version,
        generator_version=settings.generator_version,
        env=settings.app_env,
    )
