"""Idempotent catalog seeding.

Usage: python -m scripts.seed
"""

import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.models.catalog import Equipment, Exercise, ExerciseEquipment  # noqa: E402
from app.db.session import async_session_factory  # noqa: E402

SEEDS_DIR = Path(__file__).resolve().parent.parent / "seeds"


async def run_seed() -> None:
    async with async_session_factory() as session:
        equipment_data = json.loads((SEEDS_DIR / "equipment.json").read_text())
        for item in equipment_data:
            existing = await session.scalar(select(Equipment).where(Equipment.slug == item["slug"]))
            if existing is None:
                session.add(
                    Equipment(slug=item["slug"], name=item["name"], category=item["category"])
                )
            else:
                existing.name = item["name"]
                existing.category = item["category"]
                existing.active = True

        exercises_data = json.loads((SEEDS_DIR / "exercises.json").read_text())
        for item in exercises_data:
            existing = await session.scalar(select(Exercise).where(Exercise.slug == item["slug"]))
            if existing is None:
                exercise = Exercise(
                    slug=item["slug"],
                    name=item["name"],
                    workout_type=item["workout_type"],
                    movement_pattern=item["movement_pattern"],
                    primary_muscle_groups=item["primary"],
                    secondary_muscle_groups=item.get("secondary", []),
                    difficulty=item["difficulty"],
                    is_unilateral=item.get("unilateral", False),
                    default_rest_seconds=item.get("rest", 60),
                    metadata={"timed": item.get("timed", False)},
                )
                session.add(exercise)
                await session.flush()
            else:
                exercise = existing
                exercise.name = item["name"]
                exercise.workout_type = item["workout_type"]
                exercise.movement_pattern = item["movement_pattern"]
                exercise.primary_muscle_groups = item["primary"]
                exercise.secondary_muscle_groups = item.get("secondary", [])
                exercise.difficulty = item["difficulty"]
                exercise.is_unilateral = item.get("unilateral", False)
                exercise.default_rest_seconds = item.get("rest", 60)
                exercise.meta = {"timed": item.get("timed", False)}
                exercise.active = True

            equipment_by_slug: dict[str, Equipment] = {}
            for equipment in (
                await session.execute(
                    select(Equipment).where(Equipment.slug.in_(item["equipment"]))
                )
            ).scalars():
                equipment_by_slug[equipment.slug] = equipment
            for slug in item["equipment"]:
                equipment = equipment_by_slug.get(slug)
                if equipment is None:
                    raise RuntimeError(f"Unknown equipment slug {slug} for {item['slug']}")
                link = await session.get(
                    ExerciseEquipment, {"exercise_id": exercise.id, "equipment_id": equipment.id}
                )
                if link is None:
                    session.add(
                        ExerciseEquipment(exercise_id=exercise.id, equipment_id=equipment.id)
                    )
        await session.commit()
        print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(run_seed())
