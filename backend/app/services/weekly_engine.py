"""Weekly engine (section 21, Phase 2).

Deterministic aggregation first: consistency, recovery, energy, soreness, and RPE
are computed from stored user data. The LLM may only turn these facts into
readable Deep Insight sections; it never invents metrics.
"""

import datetime as dt
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProviderError, get_provider, log_provider_failure
from app.core.dates import date_range, week_start_of
from app.core.enums import VolumeDirection
from app.core.exceptions import AppError, ErrorCode
from app.db.models.weekly import WeeklySummary
from app.repositories.checkins import CheckInRepository
from app.repositories.profiles import TrainingProfileRepository
from app.repositories.sessions import SessionRepository
from app.repositories.weekly import WeeklyRepository
from app.repositories.workouts import WorkoutRepository
from app.rules.recovery import compute_recovery_score
from app.services.progress import completed_local_dates, planned_days_in_window


def _week_window(week_start: dt.date) -> list[dt.date]:
    return date_range(week_start, week_start + dt.timedelta(days=6))


async def aggregate_week(
    session: AsyncSession, user_id: uuid.UUID, week_start: dt.date, tz_name: str
) -> dict:
    checkin_repo = CheckInRepository(session)
    session_repo = SessionRepository(session)
    training_repo = TrainingProfileRepository(session)
    workout_repo = WorkoutRepository(session)

    week_end = week_start + dt.timedelta(days=6)
    days = _week_window(week_start)

    check_ins = await checkin_repo.list_in_range(user_id, week_start, week_end)
    recovery_scores = [
        compute_recovery_score(
            c.energy_score, c.sleep_score, c.mood_score, c.stress_score, c.pain_score
        )
        for c in check_ins
    ]
    energy_scores = [c.energy_score for c in check_ins]
    sleep_scores = [c.sleep_score for c in check_ins]
    stress_scores = [c.stress_score for c in check_ins]
    pain_scores = [c.pain_score for c in check_ins if c.pain_score is not None]
    max_soreness = [max(c.soreness_map.values()) if c.soreness_map else 0 for c in check_ins]

    sessions_completed = await session_repo.completed_in_range(user_id, week_start, week_end)
    rpes = [s.rpe for s in sessions_completed if s.rpe is not None]

    intensity_mix: dict[str, int] = {}
    for workout_session in sessions_completed:
        plan, _ = await workout_repo.get(user_id, workout_session.workout_plan_id)
        if plan is not None:
            intensity_mix[plan.intensity] = intensity_mix.get(plan.intensity, 0) + 1

    training = await training_repo.get(user_id)
    preferred = training.preferred_days if training else []
    planned = planned_days_in_window(preferred, days)
    completed_dates = await completed_local_dates(session, user_id, days, tz_name)
    sessions_planned = len(planned)
    sessions_completed_count = len(completed_dates & planned)

    consistency = (
        round(sessions_completed_count / sessions_planned * 100, 1) if sessions_planned else 0.0
    )

    def avg(values: list) -> float | None:
        return round(sum(values) / len(values), 1) if values else None

    metrics = {
        "checkins_count": len(check_ins),
        "sessions_planned": sessions_planned,
        "sessions_completed": sessions_completed_count,
        "avg_recovery": avg(recovery_scores),
        "avg_energy": avg(energy_scores),
        "avg_sleep": avg(sleep_scores),
        "avg_stress": avg(stress_scores),
        "avg_pain": avg(pain_scores),
        "avg_max_soreness": avg(max_soreness),
        "avg_rpe": avg(rpes),
        "intensity_mix": intensity_mix,
    }

    volume_direction = VolumeDirection.MAINTAIN.value
    if consistency >= 75 and (metrics["avg_recovery"] or 0) >= 7:
        volume_direction = VolumeDirection.UP.value
    elif consistency < 50 or (metrics["avg_recovery"] is not None and metrics["avg_recovery"] < 5):
        volume_direction = VolumeDirection.DOWN.value

    intensity_cap = None
    if (metrics["avg_pain"] is not None and metrics["avg_pain"] >= 6) or (
        metrics["avg_sleep"] is not None and metrics["avg_sleep"] <= 4
    ):
        intensity_cap = "low"

    focus_notes: list[str] = []
    if metrics["avg_max_soreness"] is not None and metrics["avg_max_soreness"] >= 7:
        focus_notes.append("Manage sore areas early in the week before increasing load.")
    if metrics["avg_sleep"] is not None and metrics["avg_sleep"] <= 5:
        focus_notes.append("Prioritize sleep and recovery before adding volume.")

    planned_adjustments = {
        "volume_direction": volume_direction,
        "intensity_cap": intensity_cap,
        "focus_notes": focus_notes,
    }

    recovery_notes = _recovery_notes(metrics)
    progression_notes = _progression_notes(consistency, metrics, volume_direction)

    return {
        "week_start": week_start,
        "week_end": week_end,
        "consistency_score": consistency,
        "recovery_notes": recovery_notes,
        "progression_notes": progression_notes,
        "planned_adjustments": planned_adjustments,
        "metrics": metrics,
    }


def _recovery_notes(metrics: dict) -> str:
    if metrics["checkins_count"] == 0:
        return "No check-ins were recorded this week, so recovery patterns are not available."
    parts = [
        f"Average recovery score was {metrics['avg_recovery']}/10.",
        f"Energy averaged {metrics['avg_energy']}/10 and sleep averaged {metrics['avg_sleep']}/10.",
    ]
    if metrics["avg_stress"] is not None:
        parts.append(f"Average stress was {metrics['avg_stress']}/10.")
    if metrics["avg_max_soreness"] is not None and metrics["avg_max_soreness"] >= 7:
        parts.append("Some areas remained highly sore during the week.")
    return " ".join(parts)


def _progression_notes(consistency: float, metrics: dict, volume_direction: str) -> str:
    planned = metrics["sessions_planned"]
    completed = metrics["sessions_completed"]
    if planned == 0:
        return "No training days were planned this week."
    notes = f"You completed {completed} of {planned} planned sessions ({consistency}% consistency)."
    if metrics["avg_rpe"] is not None:
        notes += f" Average session RPE was {metrics['avg_rpe']}/10."
    notes += f" Next week's volume direction is {volume_direction}."
    return notes


async def generate_weekly_summary(
    session: AsyncSession, user_id: uuid.UUID, week_start: dt.date, tz_name: str
) -> WeeklySummary:
    repo = WeeklyRepository(session)
    facts = await aggregate_week(session, user_id, week_start, tz_name)
    summary = await repo.upsert(
        user_id=user_id,
        week_start=facts["week_start"],
        week_end=facts["week_end"],
        consistency_score=facts["consistency_score"],
        recovery_notes=facts["recovery_notes"],
        progression_notes=facts["progression_notes"],
        planned_adjustments=facts["planned_adjustments"],
        metrics=facts["metrics"],
    )
    await session.commit()
    return summary


async def get_weekly_summary(
    session: AsyncSession, user_id: uuid.UUID, week_start: dt.date
) -> WeeklySummary:
    repo = WeeklyRepository(session)
    summary = await repo.get(user_id, week_start)
    if summary is None:
        raise AppError(
            404,
            ErrorCode.WEEKLY_SUMMARY_NOT_FOUND,
            "No weekly summary exists for this week.",
        )
    return summary


async def get_or_generate_weekly_insight(
    session: AsyncSession, user_id: uuid.UUID, week_start: dt.date
) -> dict:
    repo = WeeklyRepository(session)
    summary = await repo.get(user_id, week_start)
    if summary is None:
        raise AppError(
            404,
            ErrorCode.WEEKLY_SUMMARY_NOT_FOUND,
            "No weekly summary exists for this week.",
        )
    if summary.deep_insight:
        return summary.deep_insight

    week_facts = {
        "week_start": summary.week_start.isoformat(),
        "week_end": summary.week_end.isoformat(),
        "consistency_score": float(summary.consistency_score),
        "planned_adjustments": dict(summary.planned_adjustments or {}),
        "metrics": dict(summary.metrics or {}),
    }
    try:
        provider = get_provider()
        sections = await provider.generate_weekly_insight(week_facts)
    except (AIProviderError, AppError) as exc:
        log_provider_failure("weekly_insight", exc)
        raise AppError(
            503,
            ErrorCode.AI_INSIGHT_UNAVAILABLE,
            "The AI insight service is currently unavailable.",
        ) from exc
    await repo.save_deep_insight(summary, sections)
    await session.commit()
    return sections


def default_week_start(tz_name: str) -> dt.date:
    from app.core.dates import local_date

    return week_start_of(local_date(tz_name))
