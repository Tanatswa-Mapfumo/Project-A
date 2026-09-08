"""Unit tests for equipment filtering and candidate scoring (sections 14.7, 14.9)."""

from app.core.enums import Difficulty, ExperienceLevel, MovementPattern, WorkoutType
from app.rules.exercise_filter import (
    ExerciseCandidate,
    FilterContext,
    difficulty_allowed,
    filter_candidates,
    is_equipment_satisfied,
    muscle_excluded,
    score_candidate,
)


def make_exercise(
    exercise_id: str = "e1",
    pattern: MovementPattern = MovementPattern.SQUAT,
    equipment: list[str] | None = None,
    difficulty: Difficulty = Difficulty.BEGINNER,
    primary: list[str] | None = None,
    workout_type: WorkoutType = WorkoutType.STRENGTH,
) -> ExerciseCandidate:
    return ExerciseCandidate(
        id=exercise_id,
        slug=exercise_id,
        name=exercise_id,
        workout_type=workout_type,
        movement_pattern=pattern,
        primary_muscle_groups=primary or ["quadriceps"],
        difficulty=difficulty,
        equipment_slugs=equipment or ["bodyweight"],
    )


def test_bodyweight_always_satisfied():
    exercise = make_exercise(equipment=["bodyweight"])
    assert is_equipment_satisfied(exercise, set()) is True


def test_missing_equipment_excluded():
    exercise = make_exercise(equipment=["dumbbells"])
    assert is_equipment_satisfied(exercise, {"bodyweight"}) is False
    assert is_equipment_satisfied(exercise, {"dumbbells"}) is True


def test_owned_superset_satisfied():
    exercise = make_exercise(equipment=["dumbbells", "bench"])
    assert is_equipment_satisfied(exercise, {"dumbbells", "bench", "barbell"}) is True


def test_difficulty_allowed_by_experience():
    advanced = make_exercise(difficulty=Difficulty.ADVANCED)
    assert difficulty_allowed(advanced, ExperienceLevel.BEGINNER) is False
    assert difficulty_allowed(advanced, ExperienceLevel.ADVANCED) is True


def test_muscle_excluded():
    exercise = make_exercise(primary=["quadriceps", "glutes"])
    assert muscle_excluded(exercise, {"quadriceps"}) is True
    assert muscle_excluded(exercise, {"chest"}) is False


def test_filter_candidates_applies_all_rules():
    exercises = [
        make_exercise("a", equipment=["dumbbells"]),
        make_exercise("b", equipment=["bodyweight"], primary=["chest"]),
        make_exercise("c", equipment=["bodyweight"]),
    ]
    context = FilterContext(
        equipment_slugs=set(),
        experience_level=ExperienceLevel.BEGINNER,
        excluded_muscles={"chest"},
    )
    result = filter_candidates(exercises, context)
    assert [ex.id for ex in result] == ["c"]


def test_scoring_prefers_fresh_exercises():
    exercise = make_exercise()
    fresh = FilterContext(
        recent_exercise_ids=set(), last_session_exercise_ids=set(), equipment_slugs=set()
    )
    recent = FilterContext(
        recent_exercise_ids={"e1"},
        last_session_exercise_ids=set(),
        equipment_slugs=set(),
    )
    last = FilterContext(
        recent_exercise_ids={"e1"},
        last_session_exercise_ids={"e1"},
        equipment_slugs=set(),
    )
    assert score_candidate(exercise, fresh) > score_candidate(exercise, recent)
    assert score_candidate(exercise, recent) > score_candidate(exercise, last)


def test_scoring_penalizes_deprioritized_muscles():
    exercise = make_exercise(primary=["hamstrings"])
    context = FilterContext(
        deprioritized_muscles={"hamstrings"},
        equipment_slugs=set(),
        recent_exercise_ids=set(),
        last_session_exercise_ids=set(),
    )
    assert score_candidate(exercise, context) < 0
