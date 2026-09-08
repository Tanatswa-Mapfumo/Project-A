"""Catalog repository: equipment and exercises with join data."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.catalog import Equipment, Exercise, ExerciseEquipment
from app.rules.exercise_filter import ExerciseCandidate


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_equipment(self, active_only: bool = True) -> list[Equipment]:
        query = select(Equipment).order_by(Equipment.name)
        if active_only:
            query = query.where(Equipment.active.is_(True))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_exercises(
        self,
        workout_type: str | None = None,
        equipment_id: uuid.UUID | None = None,
        difficulty: str | None = None,
    ) -> list[Exercise]:
        query = select(Exercise).options(selectinload(Exercise.equipment_items)).distinct()
        if workout_type:
            query = query.where(Exercise.workout_type == workout_type)
        if difficulty:
            query = query.where(Exercise.difficulty == difficulty)
        if equipment_id:
            query = query.join(
                ExerciseEquipment, ExerciseEquipment.exercise_id == Exercise.id
            ).where(ExerciseEquipment.equipment_id == equipment_id)
        query = query.where(Exercise.active.is_(True)).order_by(Exercise.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_exercise(self, exercise_id: uuid.UUID) -> Exercise | None:
        result = await self.session.execute(
            select(Exercise)
            .options(selectinload(Exercise.equipment_items))
            .where(Exercise.id == exercise_id)
        )
        return result.scalar_one_or_none()

    async def count_exercises(self) -> int:
        return int(await self.session.scalar(select(func.count()).select_from(Exercise)) or 0)

    async def get_equipment_slugs_by_ids(self, equipment_ids: list[uuid.UUID]) -> list[str]:
        if not equipment_ids:
            return []
        result = await self.session.execute(
            select(Equipment.slug).where(Equipment.id.in_(equipment_ids))
        )
        return list(result.scalars().all())

    async def get_active_candidates(self) -> list[ExerciseCandidate]:
        """Load active exercises with their equipment slugs for the workout engine."""
        result = await self.session.execute(
            select(Exercise)
            .options(selectinload(Exercise.equipment_items))
            .where(Exercise.active.is_(True))
            .order_by(Exercise.slug)
        )
        exercises = list(result.scalars().all())
        candidates: list[ExerciseCandidate] = []
        for ex in exercises:
            candidates.append(
                ExerciseCandidate(
                    id=str(ex.id),
                    slug=ex.slug,
                    name=ex.name,
                    workout_type=ex.workout_type,
                    movement_pattern=ex.movement_pattern,
                    primary_muscle_groups=list(ex.primary_muscle_groups or []),
                    secondary_muscle_groups=list(ex.secondary_muscle_groups or []),
                    difficulty=ex.difficulty,
                    default_rest_seconds=ex.default_rest_seconds,
                    equipment_slugs=[e.slug for e in ex.equipment_items],
                    timed=bool((ex.meta or {}).get("timed")),
                )
            )
        return candidates
