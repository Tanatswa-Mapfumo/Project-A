"""Exercise filtering and scoring (sections 14.7, 14.8, 14.9)."""

from dataclasses import dataclass, field

from app.core.enums import Difficulty, ExperienceLevel, MovementPattern, WorkoutType
from app.rules.config import (
    DIFFICULTY_RANK,
    MAX_DIFFICULTY_BY_EXPERIENCE,
    SCORE_DEPRIORITIZED_MUSCLE,
    SCORE_FRESH_EXERCISE,
    SCORE_LAST_SESSION_REUSE,
    SCORE_RECENT_REUSE,
    UNIVERSAL_EQUIPMENT_SLUGS,
)


@dataclass
class ExerciseCandidate:
    id: str
    slug: str
    name: str
    workout_type: WorkoutType | str
    movement_pattern: MovementPattern | str
    primary_muscle_groups: list[str] = field(default_factory=list)
    secondary_muscle_groups: list[str] = field(default_factory=list)
    difficulty: Difficulty | str = Difficulty.BEGINNER
    default_rest_seconds: int = 60
    equipment_slugs: list[str] = field(default_factory=list)
    timed: bool = False

    def __post_init__(self) -> None:
        self.workout_type = WorkoutType(self.workout_type)
        self.movement_pattern = MovementPattern(self.movement_pattern)
        self.difficulty = Difficulty(self.difficulty)

    @property
    def is_timed(self) -> bool:
        return self.timed or self.workout_type in (WorkoutType.CARDIO, WorkoutType.MOBILITY)


@dataclass
class FilterContext:
    equipment_slugs: set[str] = field(default_factory=set)
    experience_level: ExperienceLevel = ExperienceLevel.BEGINNER
    excluded_muscles: set[str] = field(default_factory=set)
    deprioritized_muscles: set[str] = field(default_factory=set)
    recent_exercise_ids: set[str] = field(default_factory=set)
    last_session_exercise_ids: set[str] = field(default_factory=set)


def is_equipment_satisfied(exercise: ExerciseCandidate, equipment_slugs: set[str]) -> bool:
    required = set(exercise.equipment_slugs) - UNIVERSAL_EQUIPMENT_SLUGS
    return required <= equipment_slugs


def difficulty_allowed(exercise: ExerciseCandidate, experience_level: ExperienceLevel) -> bool:
    return DIFFICULTY_RANK[exercise.difficulty] <= MAX_DIFFICULTY_BY_EXPERIENCE[experience_level]


def muscle_excluded(exercise: ExerciseCandidate, excluded_muscles: set[str]) -> bool:
    return bool(set(exercise.primary_muscle_groups) & excluded_muscles)


def filter_candidates(
    exercises: list[ExerciseCandidate], context: FilterContext
) -> list[ExerciseCandidate]:
    return [
        ex
        for ex in exercises
        if is_equipment_satisfied(ex, context.equipment_slugs)
        and difficulty_allowed(ex, context.experience_level)
        and not muscle_excluded(ex, context.excluded_muscles)
    ]


def score_candidate(exercise: ExerciseCandidate, context: FilterContext) -> int:
    score = 0
    if set(exercise.primary_muscle_groups) & context.deprioritized_muscles:
        score += SCORE_DEPRIORITIZED_MUSCLE
    if exercise.id in context.last_session_exercise_ids:
        score += SCORE_LAST_SESSION_REUSE
    elif exercise.id in context.recent_exercise_ids:
        score += SCORE_RECENT_REUSE
    else:
        score += SCORE_FRESH_EXERCISE
    return score
