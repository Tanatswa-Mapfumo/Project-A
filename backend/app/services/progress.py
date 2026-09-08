"""Progress analytics and home aggregation (sections 19-20).

Consistency denominator (section 20.2): planned sessions are inferred from the
user's preferred training days over the last 7 local calendar days.
Streaks (section 20.3): only planned days count; unplanned rest days never break a
streak. Trends are never fabricated when data is insufficient.
"""

import datetime as dt
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dates import date_range, local_date
from app.core.enums import TrendDirection
from app.repositories.checkins import CheckInRepository
from app.repositories.profiles import TrainingProfileRepository
from app.repositories.sessions import SessionRepository
from app.repositories.workouts import WorkoutRepository
from app.rules.config import CONSISTENCY_WINDOW_DAYS, TREND_CHANGE_THRESHOLD_PERCENT
from app.rules.recovery import compute_recovery_score
from app.schemas.progress import HomeOut, HomeTodayWorkout, ProgressOut, TrendOut
from app.schemas.workout import WorkoutListItem

WEEKDAY_ENUM = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}

MIN_CHECKINS_FOR_TREND = 3


async def _training_profile(session: AsyncSession, user_id: uuid.UUID):
    repo = TrainingProfileRepository(session)
    return await repo.get(user_id)


def planned_days_in_window(preferred_days: list[str], days: list[dt.date]) -> set[dt.date]:
    preferred = set(preferred_days or [])
    return {day for day in days if WEEKDAY_ENUM[day.weekday()] in preferred}


async def completed_local_dates(
    session: AsyncSession, user_id: uuid.UUID, days: list[dt.date], tz_name: str
) -> set[dt.date]:
    repo = SessionRepository(session)
    if not days:
        return set()
    return await repo.completed_dates_in_range(user_id, days[0], days[-1], tz_name)


async def get_consistency_score(session: AsyncSession, user_id: uuid.UUID, tz_name: str) -> float:
    training = await _training_profile(session, user_id)
    today = local_date(tz_name)
    days = date_range(today - dt.timedelta(days=CONSISTENCY_WINDOW_DAYS - 1), today)
    planned = planned_days_in_window(training.preferred_days if training else [], days)
    if not planned:
        return 0.0
    completed = await completed_local_dates(session, user_id, days, tz_name)
    score = len(completed & planned) / len(planned) * 100
    return round(min(score, 100.0), 1)


async def planned_sessions_7d(session: AsyncSession, user_id: uuid.UUID, tz_name: str) -> int:
    training = await _training_profile(session, user_id)
    today = local_date(tz_name)
    days = date_range(today - dt.timedelta(days=CONSISTENCY_WINDOW_DAYS - 1), today)
    return len(planned_days_in_window(training.preferred_days if training else [], days))


async def completed_sessions_7d(session: AsyncSession, user_id: uuid.UUID, tz_name: str) -> int:
    repo = SessionRepository(session)
    today = local_date(tz_name)
    start = today - dt.timedelta(days=CONSISTENCY_WINDOW_DAYS - 1)
    return await repo.count_completed_between(user_id, start, today)


async def current_streak(session: AsyncSession, user_id: uuid.UUID, tz_name: str) -> int:
    training = await _training_profile(session, user_id)
    preferred = set(training.preferred_days if training else [])
    if not preferred:
        return 0
    today = local_date(tz_name)
    days = date_range(today - dt.timedelta(days=365), today)
    completed = await completed_local_dates(session, user_id, days, tz_name)

    streak = 0
    for offset in range(0, 366):
        day = today - dt.timedelta(days=offset)
        if WEEKDAY_ENUM[day.weekday()] not in preferred:
            continue  # rest day: never breaks a streak
        if day in completed:
            streak += 1
        elif day != today:
            break  # planned day missed
    return streak


async def _trend(session: AsyncSession, user_id: uuid.UUID, tz_name: str, metric: str) -> TrendOut:
    repo = CheckInRepository(session)
    today = local_date(tz_name)
    recent_start = today - dt.timedelta(days=13)
    check_ins = await repo.list_in_range(user_id, recent_start, today)
    by_date = {c.checkin_date: c for c in check_ins}

    def averages(days: list[dt.date]) -> list[float]:
        values: list[float] = []
        for day in days:
            check_in = by_date.get(day)
            if check_in is None:
                continue
            if metric == "recovery":
                values.append(
                    compute_recovery_score(
                        check_in.energy_score,
                        check_in.sleep_score,
                        check_in.mood_score,
                        check_in.stress_score,
                        check_in.pain_score,
                    )
                )
            else:
                values.append(float(getattr(check_in, f"{metric}_score")))
        return values

    recent_days = date_range(today - dt.timedelta(days=6), today)
    previous_days = date_range(today - dt.timedelta(days=13), today - dt.timedelta(days=7))
    recent = averages(recent_days)
    previous = averages(previous_days)

    if len(recent) < MIN_CHECKINS_FOR_TREND or not previous:
        return TrendOut(direction=TrendDirection.INSUFFICIENT_DATA.value, change_percent=None)

    recent_avg = sum(recent) / len(recent)
    previous_avg = sum(previous) / len(previous)
    change = round((recent_avg - previous_avg) / previous_avg * 100, 1) if previous_avg else 0.0
    if change >= TREND_CHANGE_THRESHOLD_PERCENT:
        direction = TrendDirection.UP.value
    elif change <= -TREND_CHANGE_THRESHOLD_PERCENT:
        direction = TrendDirection.DOWN.value
    else:
        direction = TrendDirection.STABLE.value
    return TrendOut(direction=direction, change_percent=change)


async def get_progress(session: AsyncSession, user_id: uuid.UUID, tz_name: str) -> ProgressOut:
    return ProgressOut(
        consistency_score=await get_consistency_score(session, user_id, tz_name),
        current_streak=await current_streak(session, user_id, tz_name),
        completed_sessions_7d=await completed_sessions_7d(session, user_id, tz_name),
        planned_sessions_7d=await planned_sessions_7d(session, user_id, tz_name),
        energy_trend=await _trend(session, user_id, tz_name, "energy"),
        recovery_trend=await _trend(session, user_id, tz_name, "recovery"),
        # Load history is not yet recorded for the POC, so strength progression
        # is never fabricated (section 20.1).
        strength_progression=TrendOut(
            direction=TrendDirection.INSUFFICIENT_DATA.value, change_percent=None
        ),
    )


async def get_home(session: AsyncSession, user_id: uuid.UUID, tz_name: str) -> HomeOut:
    checkin_repo = CheckInRepository(session)
    workout_repo = WorkoutRepository(session)
    today = local_date(tz_name)

    check_in = await checkin_repo.get_for_date(user_id, today)
    plan = await workout_repo.get_for_date(user_id, today)
    today_workout = None
    if plan is not None:
        today_workout = HomeTodayWorkout(
            id=plan.id,
            type=plan.type,
            intensity=plan.intensity,
            duration_minutes=plan.duration_minutes,
            status=plan.status,
            short_explanation=plan.short_explanation,
        )
    return HomeOut(
        date=today,
        check_in_completed=check_in is not None,
        today_workout=today_workout,
        consistency_score=await get_consistency_score(session, user_id, tz_name),
        current_streak=await current_streak(session, user_id, tz_name),
        quick_stats={
            "completed_sessions_7d": await completed_sessions_7d(session, user_id, tz_name)
        },
    )


async def list_workout_history(
    session: AsyncSession, user_id: uuid.UUID, page: int, page_size: int
) -> tuple[list[dict], int]:
    workout_repo = WorkoutRepository(session)
    session_repo = SessionRepository(session)
    plans, total = await workout_repo.paginate(user_id, page, page_size)
    items: list[dict] = []
    for plan in plans:
        completed_at = None
        rpe = None
        if plan.status == "completed":
            sessions = await session_repo.completed_in_range(
                user_id,
                plan.plan_date - dt.timedelta(days=1),
                plan.plan_date + dt.timedelta(days=1),
            )
            matching = [s for s in sessions if s.workout_plan_id == plan.id]
            if matching:
                completed_at = matching[0].completed_at
                rpe = matching[0].rpe
        items.append(
            {
                "id": plan.id,
                "plan_date": plan.plan_date,
                "type": plan.type,
                "intensity": plan.intensity,
                "duration_minutes": plan.duration_minutes,
                "status": plan.status,
                "completed_at": completed_at,
                "rpe": rpe,
            }
        )
    return items, total


async def list_workout_plans(
    session: AsyncSession, user_id: uuid.UUID, page: int, page_size: int
) -> tuple[list[WorkoutListItem], int]:
    workout_repo = WorkoutRepository(session)
    plans, total = await workout_repo.paginate(user_id, page, page_size)
    items = [
        WorkoutListItem(
            id=plan.id,
            plan_date=plan.plan_date,
            type=plan.type,
            intensity=plan.intensity,
            duration_minutes=plan.duration_minutes,
            goal_tags=list(plan.goal_tags or []),
            status=plan.status,
            short_explanation=plan.short_explanation,
        )
        for plan in plans
    ]
    return items, total
