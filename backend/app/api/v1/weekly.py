"""Weekly summary endpoints (section 21, Phase 2)."""

import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TzName, rate_limit
from app.config import settings
from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.weekly import WeeklyGenerateRequest, WeeklyInsightOut, WeeklySummaryOut
from app.services import weekly_engine

router = APIRouter(prefix="/weekly", tags=["Weekly"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
User = Annotated[CurrentUser, Depends(get_current_user)]


def _parse_week_start(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


@router.get(
    "/current",
    response_model=WeeklySummaryOut,
    summary="Get this week's summary",
    description="Returns the persisted weekly summary for the user's current local week.",
    responses={404: {"description": "No summary generated yet."}},
)
async def get_current_weekly(session: DbSession, user: User, tz: TzName):
    return await weekly_engine.get_weekly_summary(
        session, uuid.UUID(user.profile_id), weekly_engine.default_week_start(tz)
    )


@router.post(
    "/generate",
    response_model=WeeklySummaryOut,
    summary="Generate a weekly summary",
    description="Aggregates the week's check-ins and sessions deterministically and "
    "persists (or refreshes) the weekly summary for the given Monday `week_start` "
    "(defaults to the current week).",
    dependencies=[
        Depends(rate_limit("weekly_generate", settings.rate_limit_weekly_generate_per_minute))
    ],
)
async def generate_weekly(body: WeeklyGenerateRequest, session: DbSession, user: User, tz: TzName):
    week_start = body.week_start or weekly_engine.default_week_start(tz)
    return await weekly_engine.generate_weekly_summary(
        session, uuid.UUID(user.profile_id), week_start, tz
    )


@router.get(
    "/{week_start}/insight",
    response_model=WeeklyInsightOut,
    summary="Get weekly Deep Insight",
    description="Returns the persisted weekly Deep Insight sections, generating them on "
    "first request.",
    responses={
        404: {"description": "No summary for this week."},
        503: {"description": "AI unavailable."},
    },
)
async def get_weekly_insight(week_start: str, session: DbSession, user: User):
    return WeeklyInsightOut(
        sections=(
            await weekly_engine.get_or_generate_weekly_insight(
                session, uuid.UUID(user.profile_id), _parse_week_start(week_start)
            )
        ).get("sections", [])
    )


@router.get(
    "/{week_start}",
    response_model=WeeklySummaryOut,
    summary="Get a weekly summary",
    description="Returns the persisted weekly summary for the requested ISO Monday date.",
    responses={404: {"description": "No summary generated for this week."}},
)
async def get_weekly(week_start: str, session: DbSession, user: User):
    return await weekly_engine.get_weekly_summary(
        session, uuid.UUID(user.profile_id), _parse_week_start(week_start)
    )
