"""Duration estimation and fitting (section 14.6).

estimate = sets * SET_TIME_SECONDS + (sets - 1) * rest + TRANSITION_SECONDS
For timed exercises: duration_seconds + TRANSITION_SECONDS.

Available time is a hard upper bound; the builder trims exercises from the end
(lowest priority first) until the estimate fits.
"""

from dataclasses import dataclass

from app.rules.config import SET_TIME_SECONDS, TRANSITION_SECONDS


@dataclass
class ExerciseDraft:
    exercise_id: str
    slug: str
    name: str
    position: int
    sets: int | None
    reps_min: int | None
    reps_max: int | None
    duration_seconds: int | None
    rest_seconds: int | None
    adaptation_tags: list[str]
    estimated_seconds: int


def estimate_exercise_seconds(
    sets: int | None,
    rest_seconds: int | None,
    duration_seconds: int | None,
) -> int:
    if duration_seconds is not None and sets is None:
        return duration_seconds + TRANSITION_SECONDS
    sets = sets or 1
    rest = rest_seconds or 0
    return sets * SET_TIME_SECONDS + (sets - 1) * rest + TRANSITION_SECONDS


def total_estimated_seconds(exercises: list[ExerciseDraft]) -> int:
    return sum(ex.estimated_seconds for ex in exercises)


def fit_duration(exercises: list[ExerciseDraft], budget_seconds: int) -> list[ExerciseDraft]:
    """Trim exercises from the end until the estimate fits the budget."""
    trimmed = list(exercises)
    while len(trimmed) > 1 and total_estimated_seconds(trimmed) > budget_seconds:
        trimmed.pop()
    return trimmed
