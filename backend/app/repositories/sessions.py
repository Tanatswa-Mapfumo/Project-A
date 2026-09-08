"""Workout session repository."""

import datetime as dt
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.session import WorkoutSession


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: uuid.UUID, workout_plan_id: uuid.UUID) -> WorkoutSession:
        workout_session = WorkoutSession(
            user_id=user_id,
            workout_plan_id=workout_plan_id,
            started_at=dt.datetime.now(dt.UTC),
            status="in_progress",
        )
        self.session.add(workout_session)
        await self.session.flush()
        return workout_session

    async def get(self, user_id: uuid.UUID, session_id: uuid.UUID) -> WorkoutSession | None:
        result = await self.session.execute(
            select(WorkoutSession).where(
                WorkoutSession.id == session_id, WorkoutSession.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_in_progress_for_plan(
        self, user_id: uuid.UUID, workout_plan_id: uuid.UUID
    ) -> WorkoutSession | None:
        result = await self.session.execute(
            select(WorkoutSession).where(
                WorkoutSession.user_id == user_id,
                WorkoutSession.workout_plan_id == workout_plan_id,
                WorkoutSession.status == "in_progress",
            )
        )
        return result.scalar_one_or_none()

    async def count_completed_between(
        self, user_id: uuid.UUID, start: dt.date, end: dt.date
    ) -> int:
        start_dt = dt.datetime.combine(start, dt.time.min, tzinfo=dt.UTC)
        end_dt = dt.datetime.combine(end, dt.time.max, tzinfo=dt.UTC)
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(WorkoutSession)
                .where(
                    WorkoutSession.user_id == user_id,
                    WorkoutSession.completed.is_(True),
                    WorkoutSession.completed_at >= start_dt,
                    WorkoutSession.completed_at <= end_dt,
                )
            )
            or 0
        )

    async def completed_in_range(
        self, user_id: uuid.UUID, start: dt.date, end: dt.date
    ) -> list[WorkoutSession]:
        start_dt = dt.datetime.combine(start, dt.time.min, tzinfo=dt.UTC)
        end_dt = dt.datetime.combine(end, dt.time.max, tzinfo=dt.UTC)
        result = await self.session.execute(
            select(WorkoutSession).where(
                WorkoutSession.user_id == user_id,
                WorkoutSession.completed.is_(True),
                WorkoutSession.completed_at >= start_dt,
                WorkoutSession.completed_at <= end_dt,
            )
        )
        return list(result.scalars().all())

    async def completed_dates_in_range(
        self, user_id: uuid.UUID, start: dt.date, end: dt.date, tz_name: str
    ) -> set[dt.date]:
        """Completed-session dates resolved in the user's local timezone."""
        sessions = await self.completed_in_range(user_id, start, end)
        from app.core.dates import resolve_timezone

        tz = resolve_timezone(tz_name)
        dates: set[dt.date] = set()
        for workout_session in sessions:
            if workout_session.completed_at:
                local = workout_session.completed_at.astimezone(tz).date()
                if start <= local <= end:
                    dates.add(local)
        return dates
