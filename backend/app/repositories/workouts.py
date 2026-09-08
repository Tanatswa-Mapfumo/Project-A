"""Workout plan, exercise, and explanation repositories."""

import datetime as dt
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.session import WorkoutSession  # noqa: F401  (re-export convenience)
from app.db.models.workout import WorkoutExercise, WorkoutExplanation, WorkoutPlan


class WorkoutRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_plan(
        self,
        *,
        user_id: uuid.UUID,
        check_in_id: uuid.UUID,
        plan_date: dt.date,
        workout_type: str,
        intensity: str,
        duration_minutes: int,
        goal_tags: list[str],
        generator_version: str,
        rule_trace: dict,
        generation_metadata: dict,
    ) -> WorkoutPlan:
        plan = WorkoutPlan(
            user_id=user_id,
            check_in_id=check_in_id,
            plan_date=plan_date,
            type=workout_type,
            intensity=intensity,
            duration_minutes=duration_minutes,
            goal_tags=goal_tags,
            generator_version=generator_version,
            rule_trace=rule_trace,
            generation_metadata=generation_metadata,
        )
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def add_exercise(
        self,
        workout_plan_id: uuid.UUID,
        exercise_id: uuid.UUID,
        position: int,
        sets: int | None,
        reps_min: int | None,
        reps_max: int | None,
        duration_seconds: int | None,
        rest_seconds: int | None,
        adaptation_tags: list[str],
    ) -> WorkoutExercise:
        row = WorkoutExercise(
            workout_plan_id=workout_plan_id,
            exercise_id=exercise_id,
            position=position,
            sets=sets,
            reps_min=reps_min,
            reps_max=reps_max,
            duration_seconds=duration_seconds,
            load_kg=None,
            rest_seconds=rest_seconds,
            adaptation_tags=adaptation_tags,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get(
        self, user_id: uuid.UUID, workout_id: uuid.UUID
    ) -> tuple[WorkoutPlan | None, list[WorkoutExercise]]:
        plan = await self.session.scalar(
            select(WorkoutPlan).where(WorkoutPlan.id == workout_id, WorkoutPlan.user_id == user_id)
        )
        if plan is None:
            return None, []
        result = await self.session.execute(
            select(WorkoutExercise)
            .where(WorkoutExercise.workout_plan_id == workout_id)
            .order_by(WorkoutExercise.position)
        )
        return plan, list(result.scalars().all())

    async def get_by_check_in(
        self, user_id: uuid.UUID, check_in_id: uuid.UUID
    ) -> WorkoutPlan | None:
        result = await self.session.execute(
            select(WorkoutPlan).where(
                WorkoutPlan.user_id == user_id, WorkoutPlan.check_in_id == check_in_id
            )
        )
        return result.scalar_one_or_none()

    async def get_for_date(self, user_id: uuid.UUID, plan_date: dt.date) -> WorkoutPlan | None:
        result = await self.session.execute(
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id, WorkoutPlan.plan_date == plan_date)
            .order_by(WorkoutPlan.created_at.desc())
        )
        return result.scalars().first()

    async def paginate(
        self, user_id: uuid.UUID, page: int, page_size: int
    ) -> tuple[list[WorkoutPlan], int]:
        total = await self.session.scalar(
            select(func.count()).select_from(WorkoutPlan).where(WorkoutPlan.user_id == user_id)
        )
        result = await self.session.execute(
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id)
            .order_by(WorkoutPlan.plan_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    async def recent_completed_plans(self, user_id: uuid.UUID, limit: int = 3) -> list[WorkoutPlan]:
        result = await self.session.execute(
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id, WorkoutPlan.status == "completed")
            .order_by(WorkoutPlan.plan_date.desc(), WorkoutPlan.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def recent_exercise_ids(
        self, user_id: uuid.UUID, lookback: int = 3
    ) -> tuple[set[str], set[str]]:
        """Return (last_session_exercise_ids, recent_exercise_ids) for history
        de-prioritization (section 14.9)."""
        plans = await self.recent_completed_plans(user_id, lookback)
        last_session_ids: set[str] = set()
        recent_ids: set[str] = set()
        for index, plan in enumerate(plans):
            result = await self.session.execute(
                select(WorkoutExercise.exercise_id).where(
                    WorkoutExercise.workout_plan_id == plan.id
                )
            )
            ids = {str(row) for row in result.scalars().all()}
            recent_ids.update(ids)
            if index == 0:
                last_session_ids.update(ids)
        return last_session_ids, recent_ids

    async def update_status(self, plan: WorkoutPlan, status: str) -> None:
        plan.status = status
        await self.session.flush()

    async def get_explanation(self, workout_plan_id: uuid.UUID) -> WorkoutExplanation | None:
        result = await self.session.execute(
            select(WorkoutExplanation).where(WorkoutExplanation.workout_plan_id == workout_plan_id)
        )
        return result.scalar_one_or_none()

    async def upsert_explanation(
        self,
        workout_plan_id: uuid.UUID,
        provider: str,
        model: str,
        short_text: str,
        source_facts: dict,
    ) -> WorkoutExplanation:
        explanation = await self.get_explanation(workout_plan_id)
        if explanation is None:
            explanation = WorkoutExplanation(
                workout_plan_id=workout_plan_id,
                provider=provider,
                model=model,
                short_text=short_text,
                source_facts=source_facts,
            )
            self.session.add(explanation)
        else:
            explanation.provider = provider
            explanation.model = model
            explanation.short_text = short_text
            explanation.source_facts = source_facts
        await self.session.flush()
        return explanation

    async def save_deep_insight(self, explanation: WorkoutExplanation, sections: dict) -> None:
        explanation.deep_insight = sections
        await self.session.flush()
