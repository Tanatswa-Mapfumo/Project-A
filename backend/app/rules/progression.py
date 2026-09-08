"""Goal, experience, and progression prescription helpers (sections 14.4, 14.5, 14.9)."""

from app.core.enums import ExperienceLevel, Intensity, PrimaryGoal, WorkoutType
from app.rules.config import (
    EXPERIENCE_EXERCISE_COUNT,
    EXPERIENCE_SETS,
    GOAL_REP_RANGES,
    GOAL_WORKOUT_TYPE,
    MAX_EXERCISES,
    MIN_EXERCISES,
    REFERENCE_DURATION_MINUTES,
    STRONGER_MIN_REST_SECONDS,
)


def workout_type_for_goal(goal: PrimaryGoal) -> WorkoutType:
    return GOAL_WORKOUT_TYPE[goal]


def rep_range_for_goal(goal: PrimaryGoal) -> tuple[int, int] | None:
    return GOAL_REP_RANGES[goal]


def sets_for_experience(experience: ExperienceLevel, intensity: Intensity) -> int:
    sets = EXPERIENCE_SETS[experience]
    if intensity == Intensity.LOW:
        sets = max(1, sets - 1)
    return sets


def rest_seconds_for(goal: PrimaryGoal, default_rest_seconds: int, is_timed: bool) -> int | None:
    if is_timed:
        return None
    if goal == PrimaryGoal.GET_STRONGER:
        return max(default_rest_seconds, STRONGER_MIN_REST_SECONDS)
    return default_rest_seconds


def target_exercise_count(experience: ExperienceLevel, duration_minutes: int) -> int:
    base = EXPERIENCE_EXERCISE_COUNT[experience]
    scaled = round(base * duration_minutes / REFERENCE_DURATION_MINUTES)
    return max(MIN_EXERCISES, min(MAX_EXERCISES, scaled))
