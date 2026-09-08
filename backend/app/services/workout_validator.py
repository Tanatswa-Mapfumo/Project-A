"""Workout plan validator (section 15).

Runs before persistence. Pure function: takes the draft, the constraints, and the
catalog so it can be unit tested without a database.
"""

from app.core.enums import Intensity, WorkoutType
from app.rules.config import UNIVERSAL_EQUIPMENT_SLUGS
from app.rules.duration import total_estimated_seconds
from app.rules.exercise_filter import ExerciseCandidate
from app.services.adaptation_engine import Constraints, PlanDraft

DURATION_TOLERANCE_SECONDS = 5


def validate_plan(
    draft: PlanDraft,
    constraints: Constraints,
    catalog: list[ExerciseCandidate],
) -> list[str]:
    """Return a list of validation errors; an empty list means the plan is valid."""
    errors: list[str] = []
    catalog_map = {ex.id: ex for ex in catalog}

    if draft.workout_type not in WorkoutType:
        errors.append(f"Invalid workout type: {draft.workout_type}")
    if draft.intensity not in Intensity:
        errors.append(f"Invalid intensity: {draft.intensity}")

    if not draft.exercises:
        errors.append("Plan contains no exercises.")
        return errors

    if draft.duration_minutes != constraints.time_budget_minutes:
        errors.append(
            f"Duration {draft.duration_minutes} does not match the time budget "
            f"{constraints.time_budget_minutes}."
        )

    positions = [ex.position for ex in draft.exercises]
    if positions != list(range(1, len(positions) + 1)):
        errors.append("Exercise positions must be unique and sequential starting at 1.")

    exercise_ids = [ex.exercise_id for ex in draft.exercises]
    if len(set(exercise_ids)) != len(exercise_ids):
        errors.append("Duplicate exercises in plan.")

    for ex in draft.exercises:
        candidate = catalog_map.get(ex.exercise_id)
        if candidate is None:
            errors.append(f"Unknown exercise id: {ex.exercise_id}")
            continue

        required = set(candidate.equipment_slugs) - UNIVERSAL_EQUIPMENT_SLUGS
        if not required <= constraints.equipment_slugs:
            errors.append(f"Exercise {candidate.slug} requires unavailable equipment.")

        if set(candidate.primary_muscle_groups) & constraints.soreness.excluded_muscles:
            errors.append(f"Exercise {candidate.slug} loads an excluded sore region.")

        if ex.duration_seconds is not None:
            if ex.duration_seconds <= 0:
                errors.append(f"Exercise {candidate.slug} has non-positive duration.")
            if ex.sets is not None or ex.reps_min is not None or ex.reps_max is not None:
                errors.append(f"Timed exercise {candidate.slug} also has sets/reps.")
        else:
            if ex.sets is None or ex.sets <= 0:
                errors.append(f"Exercise {candidate.slug} has invalid sets.")
            if ex.reps_min is None or ex.reps_max is None:
                errors.append(f"Exercise {candidate.slug} has no rep range.")
            elif not (0 < ex.reps_min <= ex.reps_max):
                errors.append(f"Exercise {candidate.slug} has an invalid rep range.")

    estimated = total_estimated_seconds(draft.exercises)
    budget_seconds = constraints.time_budget_minutes * 60
    if estimated > budget_seconds + DURATION_TOLERANCE_SECONDS:
        errors.append(f"Estimated duration {estimated}s exceeds the {budget_seconds}s budget.")
    return errors
