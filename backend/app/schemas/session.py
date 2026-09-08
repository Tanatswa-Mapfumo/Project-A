"""Workout session schemas."""

import datetime as dt
import uuid

from pydantic import AliasChoices, Field, field_validator

from app.schemas.checkin import CANONICAL_REGIONS
from app.schemas.common import APIModel
from app.schemas.workout import DailySummary


class SessionStartRequest(APIModel):
    workout_id: uuid.UUID


class SessionCompleteRequest(APIModel):
    rpe: int = Field(ge=1, le=10)
    modifications: list[str] = Field(default_factory=list, max_length=20)
    post_soreness_map: dict[str, int] = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("post_soreness_map")
    @classmethod
    def validate_soreness(cls, value: dict) -> dict:
        for region, score in value.items():
            if region not in CANONICAL_REGIONS:
                raise ValueError(f"Unknown body region: {region}.")
            if not 1 <= score <= 10:
                raise ValueError(f"Soreness score for {region} must be between 1 and 10.")
        return value

    @field_validator("modifications")
    @classmethod
    def validate_modifications(cls, value: list[str]) -> list[str]:
        for item in value:
            if not item or len(item) > 80:
                raise ValueError("Modification entries must be 1-80 characters.")
        return value


class SessionQuitRequest(APIModel):
    notes: str | None = Field(default=None, max_length=2000)


class SessionOut(APIModel):
    id: uuid.UUID
    workout_id: uuid.UUID = Field(
        validation_alias=AliasChoices("workout_plan_id", "workout_id"),
        serialization_alias="workout_id",
    )
    status: str
    started_at: dt.datetime
    completed_at: dt.datetime | None = None
    completed: bool = False
    rpe: int | None = None
    modifications: list[str] = Field(default_factory=list)
    post_soreness_map: dict = Field(default_factory=dict)
    notes: str | None = None


class SessionCompleteOut(APIModel):
    session: SessionOut
    daily_summary: DailySummary
