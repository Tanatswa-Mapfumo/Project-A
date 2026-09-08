"""Unit tests for the deterministic adaptation engine (sections 14-15)."""

import datetime as dt

import pytest

from app.core.enums import WorkoutType
from app.core.exceptions import AppError, ErrorCode
from app.rules.duration import total_estimated_seconds
from app.rules.exercise_filter import ExerciseCandidate
from app.services.adaptation_engine import (
    EngineInputs,
    build_constraints,
    build_fallback_plan,
    build_plan,
    build_rule_trace,
)
from app.services.workout_validator import validate_plan


def make_exercise(
    slug: str,
    pattern: str,
    primary: list[str],
    equipment: list[str] | None = None,
    workout_type: str = "strength",
    difficulty: str = "beginner",
    rest: int = 60,
    timed: bool = False,
) -> ExerciseCandidate:
    return ExerciseCandidate(
        id=slug,
        slug=slug,
        name=slug.replace("_", " ").title(),
        workout_type=workout_type,
        movement_pattern=pattern,
        primary_muscle_groups=primary,
        difficulty=difficulty,
        default_rest_seconds=rest,
        equipment_slugs=equipment or ["bodyweight"],
        timed=timed,
    )


CATALOG = [
    make_exercise("goblet_squat", "squat", ["quadriceps"], ["dumbbells"]),
    make_exercise("bodyweight_squat", "squat", ["quadriceps"], ["bodyweight"]),
    make_exercise("romanian_deadlift", "hinge", ["hamstrings"], ["dumbbells"]),
    make_exercise("dumbbell_bench_press", "horizontal_push", ["chest"], ["dumbbells", "bench"]),
    make_exercise("push_up", "horizontal_push", ["chest"], ["bodyweight"]),
    make_exercise("overhead_press", "vertical_push", ["front_delts"], ["dumbbells"]),
    make_exercise("one_arm_dumbbell_row", "horizontal_pull", ["lats"], ["dumbbells"]),
    make_exercise("lat_pulldown", "vertical_pull", ["lats"], ["cable_machine"]),
    make_exercise("plank", "core", ["core"], ["bodyweight"], timed=True),
    make_exercise("walking", "cardio", [], ["bodyweight"], workout_type="cardio", timed=True),
    make_exercise(
        "hip_flexor_stretch",
        "mobility",
        ["hip_flexors"],
        ["bodyweight"],
        workout_type="mobility",
        timed=True,
    ),
]


def make_inputs(**overrides) -> EngineInputs:
    base = dict(
        energy_score=7,
        mood_score=7,
        sleep_score=7,
        stress_score=4,
        pain_score=None,
        soreness_map={},
        time_available_minutes=45,
        primary_goal="gain_muscle",
        experience_level="beginner",
        session_length_minutes=45,
        equipment_slugs=["dumbbells", "bench"],
        recent_exercise_ids=set(),
        last_session_exercise_ids=set(),
    )
    base.update(overrides)
    return EngineInputs(**base)


def test_constraints_recovery_and_intensity():
    constraints = build_constraints(make_inputs(energy_score=7, sleep_score=7, stress_score=4))
    assert constraints.recovery_score > 0
    assert constraints.intensity.value in ("moderate", "high")
    assert constraints.time_budget_minutes == 45
    assert any("Recovery score" in fact for fact in constraints.decision_facts)


def test_pain_restriction_raises_controlled_error():
    with pytest.raises(AppError) as exc_info:
        build_constraints(make_inputs(pain_score=9))
    assert exc_info.value.code == ErrorCode.WORKOUT_GENERATION_RESTRICTED


def test_sore_quads_excludes_quad_dominant_exercises():
    inputs = make_inputs(soreness_map={"quads": 9})
    constraints = build_constraints(inputs)
    draft = build_plan(constraints, CATALOG)
    assert draft.exercises, "plan should not be empty"
    for ex in draft.exercises:
        candidate = next(c for c in CATALOG if c.id == ex.exercise_id)
        assert "quadriceps" not in candidate.primary_muscle_groups
    errors = validate_plan(draft, constraints, CATALOG)
    assert errors == []


def test_plan_fits_time_budget():
    constraints = build_constraints(make_inputs(time_available_minutes=15))
    draft = build_plan(constraints, CATALOG)
    assert total_estimated_seconds(draft.exercises) <= 15 * 60
    assert validate_plan(draft, constraints, CATALOG) == []


def test_unavailable_equipment_never_selected():
    inputs = make_inputs(equipment_slugs=[])
    constraints = build_constraints(inputs)
    draft = build_plan(constraints, CATALOG)
    for ex in draft.exercises:
        candidate = next(c for c in CATALOG if c.id == ex.exercise_id)
        assert set(candidate.equipment_slugs) <= {"bodyweight"}


def test_plan_is_deterministic():
    first = build_plan(build_constraints(make_inputs()), CATALOG)
    second = build_plan(build_constraints(make_inputs()), CATALOG)
    assert [ex.exercise_id for ex in first.exercises] == [ex.exercise_id for ex in second.exercises]


def test_recent_history_deprioritizes_reuse():
    reused = [
        ex.exercise_id for ex in build_plan(build_constraints(make_inputs()), CATALOG).exercises
    ]
    inputs = make_inputs(
        recent_exercise_ids=set(reused),
        last_session_exercise_ids=set(reused[:2]),
    )
    draft = build_plan(build_constraints(inputs), CATALOG)
    chosen = [ex.exercise_id for ex in draft.exercises]
    assert chosen != reused[: len(chosen)]


def test_mobility_goal_uses_timed_exercises():
    inputs = make_inputs(primary_goal="improve_mobility")
    constraints = build_constraints(inputs)
    draft = build_plan(constraints, CATALOG)
    assert draft.workout_type == WorkoutType.MOBILITY
    assert all(ex.duration_seconds is not None for ex in draft.exercises)
    assert validate_plan(draft, constraints, CATALOG) == []


def test_fallback_plan_is_valid():
    inputs = make_inputs(equipment_slugs=[])
    constraints = build_constraints(inputs)
    fallback = build_fallback_plan(constraints, CATALOG)
    assert fallback.intensity.value == "low"
    assert validate_plan(fallback, constraints, CATALOG) == []


def test_rule_trace_structure():
    inputs = make_inputs(soreness_map={"quads": 9, "hamstrings": 5})
    constraints = build_constraints(inputs)
    draft = build_plan(constraints, CATALOG)
    trace = build_rule_trace(constraints, draft, inputs, dt.date(2026, 9, 8))
    assert trace["version"] == "rules-v1"
    assert trace["recovery"]["score"] == constraints.recovery_score
    assert trace["soreness"]["excluded_regions"] == ["quads"]
    assert trace["soreness"]["deprioritized_regions"] == ["hamstrings"]
    assert trace["decisions"]["intensity"] == draft.intensity.value
    assert trace["constraints"]["time_available_minutes"] == 45
    assert isinstance(trace["decision_facts"], list)


def test_beginner_gets_beginner_difficulty():
    inputs = make_inputs(experience_level="beginner", equipment_slugs=["cable_machine"])
    constraints = build_constraints(inputs)
    draft = build_plan(constraints, CATALOG)
    for ex in draft.exercises:
        candidate = next(c for c in CATALOG if c.id == ex.exercise_id)
        assert candidate.difficulty in ("beginner",)
