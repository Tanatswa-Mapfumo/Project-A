"""Catalog schemas."""

import uuid

from pydantic import Field

from app.schemas.common import APIModel


class EquipmentItem(APIModel):
    id: uuid.UUID
    slug: str
    name: str
    category: str


class EquipmentList(APIModel):
    items: list[EquipmentItem]


class ExerciseItem(APIModel):
    id: uuid.UUID
    slug: str
    name: str
    workout_type: str
    movement_pattern: str
    primary_muscle_groups: list[str]
    secondary_muscle_groups: list[str] = Field(default_factory=list)
    difficulty: str
    is_unilateral: bool = False
    default_rest_seconds: int
    equipment: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
