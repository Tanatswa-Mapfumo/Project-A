"""Progress endpoints (section 20)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TzName
from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.checkin import CheckInOut
from app.schemas.common import Page, PageParams
from app.schemas.progress import ProgressOut, WorkoutHistoryItem
from app.services import progress

router = APIRouter(prefix="/progress", tags=["Progress"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
User = Annotated[CurrentUser, Depends(get_current_user)]
PageQuery = Annotated[PageParams, Depends()]


@router.get(
    "",
    response_model=ProgressOut,
    summary="Progress overview",
    description="Consistency score, current streak, 7-day session counts, and trends. "
    "Trends return `insufficient_data` rather than fabricated values.",
)
async def get_progress(session: DbSession, user: User, tz: TzName):
    return await progress.get_progress(session, uuid.UUID(user.profile_id), tz)


@router.get(
    "/workouts",
    response_model=Page[WorkoutHistoryItem],
    summary="Workout history",
    description="Paginated workout plans with completion info, newest first.",
)
async def get_workout_history(session: DbSession, user: User, params: PageQuery):
    items, total = await progress.list_workout_history(
        session, uuid.UUID(user.profile_id), params.page, params.page_size
    )
    return Page(items=items, page=params.page, page_size=params.page_size, total=total)


@router.get(
    "/check-ins",
    response_model=Page[CheckInOut],
    summary="Check-in history",
    description="Paginated check-in history, newest first.",
)
async def get_checkin_history(session: DbSession, user: User, params: PageQuery):
    from app.services.checkins import list_check_ins

    items, total = await list_check_ins(
        session, uuid.UUID(user.profile_id), params.page, params.page_size
    )
    return Page(items=items, page=params.page, page_size=params.page_size, total=total)
