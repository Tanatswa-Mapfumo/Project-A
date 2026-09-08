"""Profile / onboarding schemas."""

import uuid
from typing import Literal

from pydantic import ConfigDict, Field

from app.schemas.common import APIModel

SESSION_LENGTHS = Literal[15, 30, 45, 60]
DAYS = Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class ProfileOut(APIModel):
    id: uuid.UUID
    email: str
    name: str | None = None
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    gender: str | None = None
    country: str | None = None
    timezone: str = "UTC"
    onboarding_completed: bool = False


class ProfileUpdate(APIModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    age: int | None = Field(default=None, ge=13, le=120)
    height_cm: float | None = Field(default=None, gt=0, le=300)
    weight_kg: float | None = Field(default=None, gt=0, le=500)
    gender: str | None = Field(default=None, max_length=80)
    country: str | None = Field(default=None, max_length=100)
    timezone: str | None = Field(default=None, max_length=64)


class GoalsIn(APIModel):
    primary_goal: Literal["lose_fat", "gain_muscle", "get_stronger", "improve_mobility"]
    secondary_goal: (
        Literal["lose_fat", "gain_muscle", "get_stronger", "improve_mobility"] | None
    ) = None
    target_metrics: dict = Field(default_factory=dict)


class GoalsOut(APIModel):
    primary_goal: str
    secondary_goal: str | None = None
    target_metrics: dict = Field(default_factory=dict)


class TrainingProfileIn(APIModel):
    experience_level: Literal["beginner", "intermediate", "advanced"]
    preferred_days: list[DAYS] = Field(default_factory=list)
    session_length_minutes: SESSION_LENGTHS


class TrainingProfileOut(APIModel):
    experience_level: str
    preferred_days: list[str] = Field(default_factory=list)
    session_length_minutes: int


class AccessibilityIn(APIModel):
    screen_reader_enabled: bool = False
    high_contrast: bool = False
    simple_mode: bool = False
    motion_reduced: bool = False
    voice_enabled: bool = False
    haptics_enabled: bool = False


class AccessibilityOut(APIModel):
    screen_reader_enabled: bool
    high_contrast: bool
    simple_mode: bool
    motion_reduced: bool
    voice_enabled: bool
    haptics_enabled: bool


class EquipmentIn(APIModel):
    equipment_ids: list[uuid.UUID] = Field(default_factory=list)


class EquipmentOut(APIModel):
    equipment_ids: list[uuid.UUID]


class NotificationsIn(APIModel):
    daily_checkin_reminders: bool = True
    workout_reminders: bool = True
    weekly_summary_alerts: bool = True


class NotificationsOut(APIModel):
    daily_checkin_reminders: bool
    workout_reminders: bool
    weekly_summary_alerts: bool


class OnboardingCompleteOut(APIModel):
    onboarding_completed: bool = True
