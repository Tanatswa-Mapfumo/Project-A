"""Check-in schemas.

Region keys and soreness value bounds are validated in the service layer so that
violations surface as CHECKIN_INVALID (not a generic VALIDATION_ERROR).
"""

import datetime as dt
import uuid

from pydantic import Field

from app.schemas.common import APIModel

CANONICAL_REGIONS = {
    "chest",
    "shoulders",
    "upper_back",
    "lower_back",
    "biceps",
    "triceps",
    "forearms",
    "core",
    "glutes",
    "quads",
    "hamstrings",
    "calves",
    "hips",
    "knees",
    "ankles",
}


class CheckInCreate(APIModel):
    energy_score: int = Field(ge=1, le=10)
    soreness_map: dict[str, int] = Field(default_factory=dict)
    mood_score: int = Field(ge=1, le=10)
    sleep_score: int = Field(ge=1, le=10)
    stress_score: int = Field(ge=1, le=10)
    time_available_minutes: int | None = Field(default=None, ge=5, le=240)
    pain_score: int | None = Field(default=None, ge=1, le=10)


class CheckInUpdate(APIModel):
    energy_score: int | None = Field(default=None, ge=1, le=10)
    soreness_map: dict[str, int] | None = None
    mood_score: int | None = Field(default=None, ge=1, le=10)
    sleep_score: int | None = Field(default=None, ge=1, le=10)
    stress_score: int | None = Field(default=None, ge=1, le=10)
    time_available_minutes: int | None = Field(default=None, ge=5, le=240)
    pain_score: int | None = Field(default=None, ge=1, le=10)


class CheckInOut(APIModel):
    id: uuid.UUID
    checkin_date: dt.date
    energy_score: int
    soreness_map: dict
    mood_score: int
    sleep_score: int
    stress_score: int
    time_available_minutes: int | None = None
    pain_score: int | None = None
    created_at: dt.datetime
