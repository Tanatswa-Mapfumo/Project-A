"""Unit tests for goal and experience prescription logic (sections 14.4, 14.5)."""

from app.core.enums import ExperienceLevel, Intensity, PrimaryGoal, WorkoutType
from app.rules.progression import (
    rep_range_for_goal,
    rest_seconds_for,
    sets_for_experience,
    target_exercise_count,
    workout_type_for_goal,
)


def test_workout_type_for_goal():
    assert workout_type_for_goal(PrimaryGoal.LOSE_FAT) == WorkoutType.MIXED
    assert workout_type_for_goal(PrimaryGoal.GAIN_MUSCLE) == WorkoutType.STRENGTH
    assert workout_type_for_goal(PrimaryGoal.GET_STRONGER) == WorkoutType.STRENGTH
    assert workout_type_for_goal(PrimaryGoal.IMPROVE_MOBILITY) == WorkoutType.MOBILITY


def test_rep_ranges():
    assert rep_range_for_goal(PrimaryGoal.LOSE_FAT) == (8, 15)
    assert rep_range_for_goal(PrimaryGoal.GAIN_MUSCLE) == (8, 12)
    assert rep_range_for_goal(PrimaryGoal.GET_STRONGER) == (4, 8)
    assert rep_range_for_goal(PrimaryGoal.IMPROVE_MOBILITY) is None


def test_sets_by_experience():
    assert sets_for_experience(ExperienceLevel.BEGINNER, Intensity.MODERATE) == 2
    assert sets_for_experience(ExperienceLevel.INTERMEDIATE, Intensity.MODERATE) == 3
    assert sets_for_experience(ExperienceLevel.ADVANCED, Intensity.MODERATE) == 4


def test_low_intensity_reduces_sets():
    assert sets_for_experience(ExperienceLevel.BEGINNER, Intensity.LOW) == 1
    assert sets_for_experience(ExperienceLevel.BEGINNER, Intensity.HIGH) == 2


def test_rest_for_stronger_goal():
    assert rest_seconds_for(PrimaryGoal.GET_STRONGER, 60, is_timed=False) == 120
    assert rest_seconds_for(PrimaryGoal.GAIN_MUSCLE, 90, is_timed=False) == 90
    assert rest_seconds_for(PrimaryGoal.GAIN_MUSCLE, 90, is_timed=True) is None


def test_target_exercise_count_scales_with_duration():
    assert target_exercise_count(ExperienceLevel.BEGINNER, 45) == 5
    assert target_exercise_count(ExperienceLevel.BEGINNER, 15) == 2
    assert target_exercise_count(ExperienceLevel.BEGINNER, 60) == 7
    assert target_exercise_count(ExperienceLevel.ADVANCED, 45) == 7
    assert target_exercise_count(ExperienceLevel.ADVANCED, 60) == 8  # capped


def test_target_exercise_count_never_below_one():
    assert target_exercise_count(ExperienceLevel.BEGINNER, 15) >= 1
