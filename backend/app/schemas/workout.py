"""Workout schemas."""

import datetime as dt
import uuid

from pydantic import Field

from app.schemas.common import APIModel


class WorkoutGenerateRequest(APIModel):
    check_in_id: uuid.UUID


class WorkoutExerciseOut(APIModel):
    id: uuid.UUID
    exercise_id: uuid.UUID
    slug: str
    name: str
    position: int
    sets: int | None = None
    reps_min: int | None = None
    reps_max: int | None = None
    duration_seconds: int | None = None
    load_kg: float | None = None
    rest_seconds: int | None = None
    notes: str | None = None
    adaptation_tags: list[str] = Field(default_factory=list)


class WorkoutOut(APIModel):
    id: uuid.UUID
    plan_date: dt.date
    type: str
    intensity: str
    duration_minutes: int
    goal_tags: list[str] = Field(default_factory=list)
    status: str
    short_explanation: str | None = None
    generator_version: str
    exercises: list[WorkoutExerciseOut] = Field(default_factory=list)


class WorkoutListItem(APIModel):
    id: uuid.UUID
    plan_date: dt.date
    type: str
    intensity: str
    duration_minutes: int
    goal_tags: list[str] = Field(default_factory=list)
    status: str
    short_explanation: str | None = None


class TodayWorkoutOut(APIModel):
    workout: WorkoutOut | None = None


class ExplanationOut(APIModel):
    workout_id: uuid.UUID
    short_explanation: str
    provider: str
    model: str
    created_at: dt.datetime


class InsightSection(APIModel):
    type: str
    title: str
    content: str


class InsightOut(APIModel):
    sections: list[InsightSection]


class DailySummary(APIModel):
    date: dt.date
    completed_sessions_today: int
    consistency_score: float
    current_streak: int
