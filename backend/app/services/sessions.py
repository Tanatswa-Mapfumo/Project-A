"""Workout session services (section 18)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, ErrorCode
from app.db.models.session import WorkoutSession
from app.repositories.sessions import SessionRepository
from app.repositories.workouts import WorkoutRepository
from app.schemas.session import SessionCompleteRequest, SessionQuitRequest
from app.services.progress import current_streak, get_consistency_score


async def start_session(
    session: AsyncSession, user_id: uuid.UUID, workout_id: uuid.UUID
) -> WorkoutSession:
    workout_repo = WorkoutRepository(session)
    session_repo = SessionRepository(session)

    plan, _ = await workout_repo.get(user_id, workout_id)
    if plan is None:
        raise AppError(404, ErrorCode.WORKOUT_NOT_FOUND, "The requested workout was not found.")
    if plan.status == "completed":
        raise AppError(
            409, ErrorCode.SESSION_INVALID_STATE, "This workout has already been completed."
        )

    in_progress = await session_repo.get_in_progress_for_plan(user_id, plan.id)
    if in_progress is not None:
        return in_progress

    workout_session = await session_repo.create(user_id, plan.id)
    await workout_repo.update_status(plan, "started")
    await session.commit()
    return workout_session


async def get_session(
    session: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID
) -> WorkoutSession:
    repo = SessionRepository(session)
    workout_session = await repo.get(user_id, session_id)
    if workout_session is None:
        raise AppError(404, ErrorCode.SESSION_NOT_FOUND, "The requested session was not found.")
    return workout_session


async def complete_session(
    session: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    payload: SessionCompleteRequest,
    tz_name: str,
) -> dict:
    import datetime as dt

    repo = SessionRepository(session)
    workout_repo = WorkoutRepository(session)
    workout_session = await repo.get(user_id, session_id)
    if workout_session is None:
        raise AppError(404, ErrorCode.SESSION_NOT_FOUND, "The requested session was not found.")
    if workout_session.completed:
        raise AppError(
            409, ErrorCode.SESSION_ALREADY_COMPLETED, "This session has already been completed."
        )
    if workout_session.status == "quit":
        raise AppError(409, ErrorCode.SESSION_INVALID_STATE, "A quit session cannot be completed.")

    workout_session.status = "completed"
    workout_session.completed = True
    workout_session.completed_at = dt.datetime.now(dt.UTC)
    workout_session.rpe = payload.rpe
    workout_session.modifications = payload.modifications
    workout_session.post_soreness_map = payload.post_soreness_map
    workout_session.notes = payload.notes

    plan, _ = await workout_repo.get(user_id, workout_session.workout_plan_id)
    if plan is not None:
        await workout_repo.update_status(plan, "completed")
    await session.commit()

    from app.core.dates import local_date

    today = local_date(tz_name)
    completed_today = await repo.count_completed_between(user_id, today, today)
    consistency = await get_consistency_score(session, user_id, tz_name)
    streak = await current_streak(session, user_id, tz_name)
    return {
        "session": workout_session,
        "daily_summary": {
            "date": today,
            "completed_sessions_today": completed_today,
            "consistency_score": consistency,
            "current_streak": streak,
        },
    }


async def quit_session(
    session: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    payload: SessionQuitRequest,
) -> WorkoutSession:
    repo = SessionRepository(session)
    workout_repo = WorkoutRepository(session)
    workout_session = await repo.get(user_id, session_id)
    if workout_session is None:
        raise AppError(404, ErrorCode.SESSION_NOT_FOUND, "The requested session was not found.")
    if workout_session.completed:
        raise AppError(
            409, ErrorCode.SESSION_ALREADY_COMPLETED, "This session has already been completed."
        )
    workout_session.status = "quit"
    workout_session.completed = False
    if payload.notes:
        workout_session.notes = payload.notes

    plan, _ = await workout_repo.get(user_id, workout_session.workout_plan_id)
    if plan is not None and plan.status == "started":
        await workout_repo.update_status(plan, "generated")
    await session.commit()
    return workout_session
