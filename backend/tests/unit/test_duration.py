"""Unit tests for duration estimation and fitting (section 14.6)."""

from app.rules.duration import (
    ExerciseDraft,
    estimate_exercise_seconds,
    fit_duration,
    total_estimated_seconds,
)


def make_draft(estimated: int, position: int = 1) -> ExerciseDraft:
    return ExerciseDraft(
        exercise_id=f"e{position}",
        slug=f"e{position}",
        name=f"e{position}",
        position=position,
        sets=3,
        reps_min=8,
        reps_max=12,
        duration_seconds=None,
        rest_seconds=60,
        adaptation_tags=[],
        estimated_seconds=estimated,
    )


def test_strength_estimate():
    # 3 sets * 40s + 2 rests * 90s + 45s transition = 120 + 180 + 45 = 345
    assert estimate_exercise_seconds(3, 90, None) == 345


def test_timed_estimate():
    assert estimate_exercise_seconds(None, None, 60) == 105


def test_total_estimated_seconds():
    drafts = [make_draft(300, 1), make_draft(300, 2)]
    assert total_estimated_seconds(drafts) == 600


def test_fit_duration_trims_from_end():
    drafts = [make_draft(400, 1), make_draft(400, 2), make_draft(400, 3)]
    result = fit_duration(drafts, 800)
    assert [d.position for d in result] == [1, 2]


def test_fit_duration_keeps_at_least_one():
    drafts = [make_draft(900, 1), make_draft(400, 2)]
    result = fit_duration(drafts, 60)
    assert len(result) == 1
