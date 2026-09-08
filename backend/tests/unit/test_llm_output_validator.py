"""Unit tests for the LLM output validator (section 16.4)."""

from app.services.explanation_engine import validate_short_explanation


def test_valid_explanation_passes():
    text = (
        "Your energy is moderate and your quads are recovering, "
        "so today's session is upper-body focused."
    )
    assert validate_short_explanation(text, ["Push Up"], []) == []


def test_empty_explanation_fails():
    assert validate_short_explanation("", [], []) != []
    assert validate_short_explanation("   ", [], []) != []


def test_too_long_fails():
    text = "word " * 300
    assert any("long" in error for error in validate_short_explanation(text, [], []))


def test_banned_medical_language_fails():
    text = "This plan will help treat your condition safely."
    errors = validate_short_explanation(text, [], [])
    assert any("disallowed" in error for error in errors)


def test_foreign_exercise_mention_fails():
    text = "Your session today includes the Barbell Deadlift for strength."
    errors = validate_short_explanation(text, ["Push Up"], ["Barbell Deadlift"])
    assert any("not in the plan" in error for error in errors)


def test_plan_exercise_mention_allowed():
    text = "Push Up is a great fit for today."
    assert validate_short_explanation(text, ["Push Up"], []) == []
