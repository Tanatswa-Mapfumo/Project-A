"""Catalog endpoints (section 11)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.exceptions import AppError, ErrorCode
from app.db.session import get_db
from app.repositories.catalog import CatalogRepository
from app.schemas.catalog import EquipmentItem, EquipmentList, ExerciseItem

router = APIRouter(prefix="/catalog", tags=["Catalog"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
User = Annotated[CurrentUser, Depends(get_current_user)]


@router.get(
    "/equipment",
    response_model=EquipmentList,
    summary="List equipment",
    description="Returns the full active equipment catalog.",
)
async def list_equipment(session: DbSession, _: User):
    repo = CatalogRepository(session)
    items = await repo.list_equipment()
    return EquipmentList(
        items=[
            EquipmentItem(id=item.id, slug=item.slug, name=item.name, category=item.category)
            for item in items
        ]
    )


@router.get(
    "/exercises",
    response_model=list[ExerciseItem],
    summary="List exercises",
    description="Lists active exercises. Optional filters: workout_type, equipment_id, "
    "difficulty. Primarily for onboarding and debugging; workout generation uses the "
    "engine internally.",
)
async def list_exercises(
    session: DbSession,
    _: User,
    workout_type: str | None = Query(default=None, description="strength|cardio|mobility|mixed"),
    equipment_id: uuid.UUID | None = Query(default=None),
    difficulty: str | None = Query(default=None, description="beginner|intermediate|advanced"),
):
    repo = CatalogRepository(session)
    exercises = await repo.list_exercises(workout_type, equipment_id, difficulty)
    return [
        ExerciseItem(
            id=ex.id,
            slug=ex.slug,
            name=ex.name,
            workout_type=ex.workout_type,
            movement_pattern=ex.movement_pattern,
            primary_muscle_groups=list(ex.primary_muscle_groups or []),
            secondary_muscle_groups=list(ex.secondary_muscle_groups or []),
            difficulty=ex.difficulty,
            is_unilateral=ex.is_unilateral,
            default_rest_seconds=ex.default_rest_seconds,
            equipment=[e.slug for e in ex.equipment_items],
            metadata=dict(ex.meta or {}),
        )
        for ex in exercises
    ]


@router.get(
    "/exercises/{exercise_id}",
    response_model=ExerciseItem,
    summary="Get an exercise",
    description="Returns one active catalog exercise with its equipment requirements.",
    responses={404: {"description": "Exercise not found."}},
)
async def get_exercise(exercise_id: uuid.UUID, session: DbSession, _: User):
    repo = CatalogRepository(session)
    ex = await repo.get_exercise(exercise_id)
    if ex is None:
        raise AppError(404, ErrorCode.EXERCISE_NOT_FOUND, "The requested exercise was not found.")
    return ExerciseItem(
        id=ex.id,
        slug=ex.slug,
        name=ex.name,
        workout_type=ex.workout_type,
        movement_pattern=ex.movement_pattern,
        primary_muscle_groups=list(ex.primary_muscle_groups or []),
        secondary_muscle_groups=list(ex.secondary_muscle_groups or []),
        difficulty=ex.difficulty,
        is_unilateral=ex.is_unilateral,
        default_rest_seconds=ex.default_rest_seconds,
        equipment=[e.slug for e in ex.equipment_items],
        metadata=dict(ex.meta or {}),
    )
