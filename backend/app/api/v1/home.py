"""Home dashboard endpoint (section 19)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TzName
from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.progress import HomeOut
from app.services import progress

router = APIRouter(tags=["Progress"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
User = Annotated[CurrentUser, Depends(get_current_user)]


@router.get(
    "/home",
    response_model=HomeOut,
    summary="Home dashboard aggregate",
    description="Single aggregation endpoint that reduces frontend request fan-out: "
    "today's check-in state, today's workout, consistency, streak, and quick stats.",
)
async def get_home(session: DbSession, user: User, tz: TzName):
    return await progress.get_home(session, uuid.UUID(user.profile_id), tz)
