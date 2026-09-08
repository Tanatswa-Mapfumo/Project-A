"""Workout generation orchestration (sections 13-16).

Deterministic engine -> validator -> persistence -> LLM explanation. The LLM only
explains the persisted plan; a provider failure never fails generation.
"""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AppError, ErrorCode
from app.core.logging import get_logger
from app.repositories.catalog import CatalogRepository
from app.repositories.checkins import CheckInRepository
from app.repositories.profiles import (
    EquipmentRepository,
    GoalsRepository,
    ProfileRepository,
    TrainingProfileRepository,
)
from app.repositories.workouts import WorkoutRepository
from app.rules.exercise_filter import ExerciseCandidate
from app.schemas.workout import WorkoutExerciseOut, WorkoutOut
from app.services.adaptation_engine import (
    EngineInputs,
    build_constraints,
    build_fallback_plan,
    build_plan,
    build_rule_trace,
)
from app.services.explanation_engine import ExplanationEngine
from app.services.workout_validator import validate_plan

logger = get_logger("app.generator")


async def _assemble_workout_out(
    plan,
    exercise_rows,
    catalog_map: dict[str, ExerciseCandidate],
) -> WorkoutOut:
    exercises_out: list[WorkoutExerciseOut] = []
    for row in exercise_rows:
        candidate = catalog_map.get(str(row.exercise_id))
        name = candidate.name if candidate else "Unknown exercise"
        slug = candidate.slug if candidate else ""
        exercises_out.append(
            WorkoutExerciseOut(
                id=row.id,
                exercise_id=row.exercise_id,
                slug=slug,
                name=name,
                position=row.position,
                sets=row.sets,
                reps_min=row.reps_min,
                reps_max=row.reps_max,
                duration_seconds=row.duration_seconds,
                load_kg=row.load_kg,
                rest_seconds=row.rest_seconds,
                notes=row.notes,
                adaptation_tags=list(row.adaptation_tags or []),
            )
        )
    return WorkoutOut(
        id=plan.id,
        plan_date=plan.plan_date,
        type=plan.type,
        intensity=plan.intensity,
        duration_minutes=plan.duration_minutes,
        goal_tags=list(plan.goal_tags or []),
        status=plan.status,
        short_explanation=plan.short_explanation,
        generator_version=plan.generator_version,
        exercises=exercises_out,
    )


async def get_workout_out(
    session: AsyncSession,
    user_id: uuid.UUID,
    workout_id: uuid.UUID,
) -> WorkoutOut:
    workout_repo = WorkoutRepository(session)
    catalog_repo = CatalogRepository(session)
    plan, rows = await workout_repo.get(user_id, workout_id)
    if plan is None:
        raise AppError(404, ErrorCode.WORKOUT_NOT_FOUND, "The requested workout was not found.")
    candidates = await catalog_repo.get_active_candidates()
    catalog_map = {c.id: c for c in candidates}
    return await _assemble_workout_out(plan, rows, catalog_map)


async def generate_workout(
    session: AsyncSession,
    user_id: uuid.UUID,
    check_in_id: uuid.UUID,
    tz_name: str,
) -> WorkoutOut:
    """Load server-side data, build, validate, persist, and explain a workout plan."""
    ProfileRepository(session)
    goals_repo = GoalsRepository(session)
    training_repo = TrainingProfileRepository(session)
    equipment_repo = EquipmentRepository(session)
    checkin_repo = CheckInRepository(session)
    workout_repo = WorkoutRepository(session)
    catalog_repo = CatalogRepository(session)

    check_in = await checkin_repo.get(user_id, check_in_id)
    if check_in is None:
        raise AppError(404, ErrorCode.CHECKIN_NOT_FOUND, "The requested check-in was not found.")

    existing = await workout_repo.get_by_check_in(user_id, check_in_id)
    if existing is not None:
        return await get_workout_out(session, user_id, existing.id)

    goal = await goals_repo.get(user_id)
    if goal is None:
        raise AppError(
            422,
            ErrorCode.ONBOARDING_INCOMPLETE,
            "A goal profile is required before generating workouts.",
            {"missing": ["goals"]},
        )
    training = await training_repo.get(user_id)
    if training is None:
        raise AppError(
            422,
            ErrorCode.ONBOARDING_INCOMPLETE,
            "A training profile is required before generating workouts.",
            {"missing": ["training_profile"]},
        )

    equipment_ids = await equipment_repo.get_ids_for_user(user_id)
    equipment_slugs = await catalog_repo.get_equipment_slugs_by_ids(equipment_ids)

    last_session_ids, recent_ids = await workout_repo.recent_exercise_ids(user_id)

    inputs = EngineInputs(
        energy_score=check_in.energy_score,
        mood_score=check_in.mood_score,
        sleep_score=check_in.sleep_score,
        stress_score=check_in.stress_score,
        pain_score=check_in.pain_score,
        soreness_map=dict(check_in.soreness_map or {}),
        time_available_minutes=check_in.time_available_minutes,
        primary_goal=goal.primary_goal,
        experience_level=training.experience_level,
        session_length_minutes=training.session_length_minutes,
        equipment_slugs=equipment_slugs,
        recent_exercise_ids=recent_ids,
        last_session_exercise_ids=last_session_ids,
    )

    constraints = build_constraints(inputs)
    catalog = await catalog_repo.get_active_candidates()

    try:
        draft = build_plan(constraints, catalog)
        source = "primary"
    except AppError as exc:
        if exc.code in (
            ErrorCode.WORKOUT_GENERATION_RESTRICTED,
            ErrorCode.WORKOUT_VALIDATION_FAILED,
        ):
            raise
        logger.exception("unexpected_plan_error")
        raise AppError(
            422,
            ErrorCode.WORKOUT_GENERATION_FAILED,
            "The workout generator failed.",
        ) from exc

    errors = validate_plan(draft, constraints, catalog)
    if errors:
        logger.warning("plan_validation_failed errors=%s", errors)
        draft = build_fallback_plan(constraints, catalog)
        source = "fallback"
        errors = validate_plan(draft, constraints, catalog)
        if errors:
            logger.error("fallback_plan_invalid errors=%s", errors)
            raise AppError(
                422,
                ErrorCode.WORKOUT_VALIDATION_FAILED,
                "The workout generator could not produce a valid plan.",
                {"suggested_action": "review_checkin"},
            )

    rule_trace = build_rule_trace(constraints, draft, inputs, check_in.checkin_date)
    generation_metadata = {
        "generator_version": settings.generator_version,
        "source": source,
        "exercise_candidates": len(catalog),
    }

    try:
        plan = await workout_repo.create_plan(
            user_id=user_id,
            check_in_id=check_in_id,
            plan_date=check_in.checkin_date,
            workout_type=draft.workout_type.value,
            intensity=draft.intensity.value,
            duration_minutes=draft.duration_minutes,
            goal_tags=draft.goal_tags,
            generator_version=settings.generator_version,
            rule_trace=rule_trace,
            generation_metadata=generation_metadata,
        )
        for row in draft.exercises:
            await workout_repo.add_exercise(
                workout_plan_id=plan.id,
                exercise_id=uuid.UUID(row.exercise_id),
                position=row.position,
                sets=row.sets,
                reps_min=row.reps_min,
                reps_max=row.reps_max,
                duration_seconds=row.duration_seconds,
                rest_seconds=row.rest_seconds,
                adaptation_tags=row.adaptation_tags,
            )
    except IntegrityError as exc:
        # Concurrent retry: another request already persisted the canonical plan.
        await session.rollback()
        existing = await workout_repo.get_by_check_in(user_id, check_in_id)
        if existing is not None:
            return await get_workout_out(session, user_id, existing.id)
        raise AppError(
            409,
            ErrorCode.WORKOUT_ALREADY_EXISTS,
            "A workout already exists for this check-in.",
        ) from exc

    explanation_engine = ExplanationEngine(session)
    catalog_map = {c.id: c for c in catalog}
    plan_names = [row.name for row in draft.exercises]
    other_names = [
        c.name for c in catalog if c.id not in {row.exercise_id for row in draft.exercises}
    ]
    await explanation_engine.generate_and_persist_short(plan, rule_trace, plan_names, other_names)
    await session.commit()

    _, rows = await workout_repo.get(user_id, plan.id)
    return await _assemble_workout_out(plan, rows, catalog_map)


async def get_rule_trace(
    session: AsyncSession,
    user_id: uuid.UUID,
    workout_id: uuid.UUID,
) -> dict:
    workout_repo = WorkoutRepository(session)
    plan, _ = await workout_repo.get(user_id, workout_id)
    if plan is None:
        raise AppError(404, ErrorCode.WORKOUT_NOT_FOUND, "The requested workout was not found.")
    return dict(plan.rule_trace or {})


async def get_explanation(
    session: AsyncSession,
    user_id: uuid.UUID,
    workout_id: uuid.UUID,
) -> dict:
    workout_repo = WorkoutRepository(session)
    plan, _ = await workout_repo.get(user_id, workout_id)
    if plan is None:
        raise AppError(404, ErrorCode.WORKOUT_NOT_FOUND, "The requested workout was not found.")
    explanation = await workout_repo.get_explanation(plan.id)
    if explanation is None:
        raise AppError(
            503,
            ErrorCode.AI_EXPLANATION_UNAVAILABLE,
            "No explanation has been generated for this workout.",
        )
    return {
        "workout_id": plan.id,
        "short_explanation": explanation.short_text,
        "provider": explanation.provider,
        "model": explanation.model,
        "created_at": explanation.created_at,
    }
