"""Weekly summary schemas (Phase 2)."""

import datetime as dt
import uuid

from pydantic import Field

from app.schemas.common import APIModel


class WeeklyGenerateRequest(APIModel):
    week_start: dt.date | None = None


class WeeklySummaryOut(APIModel):
    id: uuid.UUID
    week_start: dt.date
    week_end: dt.date
    consistency_score: float
    recovery_notes: str
    progression_notes: str
    planned_adjustments: dict = Field(default_factory=dict)
    metrics: dict = Field(default_factory=dict)
    created_at: dt.datetime


class WeeklyInsightOut(APIModel):
    sections: list[dict] = Field(default_factory=list)
