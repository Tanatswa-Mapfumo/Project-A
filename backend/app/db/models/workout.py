"""Workout plan, exercise, and explanation models."""

import datetime as dt
import uuid

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, jsonb_column


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"
    __table_args__ = (
        UniqueConstraint("user_id", "check_in_id", name="uq_workout_plans_user_checkin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("profiles.id"), nullable=False)
    check_in_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("check_ins.id"), nullable=False)
    plan_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    intensity: Mapped[str] = mapped_column(String, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    goal_tags: Mapped[list] = mapped_column(jsonb_column(), nullable=False, default=list)
    short_explanation: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, nullable=False, default="generated")
    generator_version: Mapped[str] = mapped_column(String, nullable=False)
    rule_trace: Mapped[dict] = mapped_column(jsonb_column(), nullable=False, default=dict)
    generation_metadata: Mapped[dict] = mapped_column(jsonb_column(), nullable=False, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: dt.datetime.now(dt.UTC)
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: dt.datetime.now(dt.UTC),
        onupdate=lambda: dt.datetime.now(dt.UTC),
    )


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"
    __table_args__ = (
        UniqueConstraint("workout_plan_id", "position", name="uq_workout_exercises_plan_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workout_plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workout_plans.id"), nullable=False, index=True
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("exercises.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    sets: Mapped[int | None] = mapped_column(Integer)
    reps_min: Mapped[int | None] = mapped_column(Integer)
    reps_max: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    load_kg: Mapped[float | None] = mapped_column(Numeric)
    rest_seconds: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    adaptation_tags: Mapped[list] = mapped_column(jsonb_column(), nullable=False, default=list)


class WorkoutExplanation(Base):
    __tablename__ = "workout_explanations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workout_plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workout_plans.id"), unique=True, nullable=False
    )
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    short_text: Mapped[str] = mapped_column(Text, nullable=False)
    deep_insight: Mapped[dict | None] = mapped_column(jsonb_column())
    source_facts: Mapped[dict] = mapped_column(jsonb_column(), nullable=False, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: dt.datetime.now(dt.UTC)
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: dt.datetime.now(dt.UTC),
        onupdate=lambda: dt.datetime.now(dt.UTC),
    )
