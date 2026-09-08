"""Workout generation and retrieval endpoints (sections 13, 17)."""

import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TzName, rate_limit
from app.config import settings
from app.core.auth import CurrentUser, get_current_user
from app.core.exceptions import AppError, ErrorCode
from app.db.session import get_db
from app.repositories.checkins import CheckInRepository
from app.repositories.workouts import WorkoutRepository
from app.schemas.common import Page, PageParams
from app.schemas.workout import (
    ExplanationOut,
    InsightOut,
    TodayWorkoutOut,
    WorkoutGenerateRequest,
    WorkoutListItem,
    WorkoutOut,
)
from app.services import progress as progress_service
from app.services import workout_generator
from app.services.explanation_engine import ExplanationEngine

router = APIRouter(prefix="/workouts", tags=["Workouts"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
User = Annotated[CurrentUser, Depends(get_current_user)]
PageQuery = Annotated[PageParams, Depends()]

GENERATE_EXAMPLE = {"check_in_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"}


@router.post(
    "/generate",
    response_model=WorkoutOut,
    summary="Generate today's workout",
    description="Deterministically builds an adapted workout plan from the server-side "
    "profile, equipment, check-in, and history. Idempotent: repeated calls for the same "
    "check-in return the existing plan.",
    responses={
        404: {"description": "Check-in not found."},
        409: {"description": "Plan already exists."},
        422: {"description": "Onboarding incomplete, generation restricted, or validation failed."},
    },
    dependencies=[Depends(rate_limit("workout_generate", settings.rate_limit_generate_per_minute))],
)
async def generate_workout(
    body: WorkoutGenerateRequest, session: DbSession, user: User, tz: TzName
):
    return await workout_generator.generate_workout(
        session, uuid.UUID(user.profile_id), body.check_in_id, tz
    )


@router.get(
    "/today",
    response_model=TodayWorkoutOut,
    summary="Get today's workout",
    description="Returns today's generated plan or `null` when none exists.",
)
async def get_today_workout(session: DbSession, user: User, tz: TzName):
    from app.core.dates import local_date

    plan = await WorkoutRepository(session).get_for_date(uuid.UUID(user.profile_id), local_date(tz))
    if plan is None:
        return TodayWorkoutOut(workout=None)
    workout = await workout_generator.get_workout_out(session, uuid.UUID(user.profile_id), plan.id)
    return TodayWorkoutOut(workout=workout)


@router.get(
    "",
    response_model=Page[WorkoutListItem],
    summary="List my workouts",
    description="Paginated workout plan history, newest first.",
)
async def list_workouts(session: DbSession, user: User, params: PageQuery):
    items, total = await progress_service.list_workout_plans(
        session, uuid.UUID(user.profile_id), params.page, params.page_size
    )
    return Page(items=items, page=params.page, page_size=params.page_size, total=total)


@router.get(
    "/{workout_id}",
    response_model=WorkoutOut,
    summary="Get a workout",
    description="Returns the full plan with its exercises. Cross-user access returns 404.",
    responses={404: {"description": "Workout not found."}},
)
async def get_workout(workout_id: uuid.UUID, session: DbSession, user: User):
    return await workout_generator.get_workout_out(session, uuid.UUID(user.profile_id), workout_id)


@router.get(
    "/{workout_id}/explanation",
    response_model=ExplanationOut,
    summary="Get the workout explanation",
    description="Returns the persisted short explanation for the plan.",
    responses={404: {"description": "Workout not found."}, 503: {"description": "No explanation."}},
)
async def get_explanation(workout_id: uuid.UUID, session: DbSession, user: User):
    return await workout_generator.get_explanation(session, uuid.UUID(user.profile_id), workout_id)


@router.get(
    "/{workout_id}/insight",
    response_model=InsightOut,
    summary="Get Deep Insight (Phase 2)",
    description="Generates and persists the structured Deep Insight sections on first "
    "request; subsequent reads use the persisted result.",
    responses={404: {"description": "Workout not found."}, 503: {"description": "AI unavailable."}},
    dependencies=[Depends(rate_limit("workout_insight", settings.rate_limit_insight_per_minute))],
)
async def get_insight(workout_id: uuid.UUID, session: DbSession, user: User, tz: TzName):
    workout_repo = WorkoutRepository(session)
    checkin_repo = CheckInRepository(session)
    plan, _ = await workout_repo.get(uuid.UUID(user.profile_id), workout_id)
    if plan is None:
        raise AppError(404, ErrorCode.WORKOUT_NOT_FOUND, "The requested workout was not found.")

    source_facts = dict(plan.rule_trace or {})
    check_in = await checkin_repo.get(uuid.UUID(user.profile_id), plan.check_in_id)
    avg_energy = None
    if check_in is not None:
        history = await checkin_repo.list_in_range(
            uuid.UUID(user.profile_id),
            check_in.checkin_date - dt.timedelta(days=6),
            check_in.checkin_date,
        )
        if history:
            avg_energy = round(sum(c.energy_score for c in history) / len(history), 1)
    history_summary = {
        "avg_energy_7d": avg_energy,
        "consistency_score": await progress_service.get_consistency_score(
            session, uuid.UUID(user.profile_id), tz
        ),
    }
    sections = await ExplanationEngine(session).get_or_generate_deep_insight(
        plan, source_facts, history_summary
    )
    return InsightOut(sections=sections.get("sections", []))
