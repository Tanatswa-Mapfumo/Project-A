"""Progress and home dashboard schemas."""

import datetime as dt
import uuid

from pydantic import Field

from app.schemas.common import APIModel


class TrendOut(APIModel):
    direction: str
    change_percent: float | None = None


class ProgressOut(APIModel):
    consistency_score: float
    current_streak: int
    completed_sessions_7d: int
    planned_sessions_7d: int
    energy_trend: TrendOut
    recovery_trend: TrendOut
    strength_progression: TrendOut


class HomeTodayWorkout(APIModel):
    id: uuid.UUID
    type: str
    intensity: str
    duration_minutes: int
    status: str
    short_explanation: str | None = None


class HomeOut(APIModel):
    date: dt.date
    check_in_completed: bool
    today_workout: HomeTodayWorkout | None = None
    consistency_score: float
    current_streak: int
    quick_stats: dict = Field(default_factory=dict)


class WorkoutHistoryItem(APIModel):
    id: uuid.UUID
    plan_date: dt.date
    type: str
    intensity: str
    duration_minutes: int
    status: str
    completed_at: dt.datetime | None = None
    rpe: int | None = None
