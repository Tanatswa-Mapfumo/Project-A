"""Deterministic adaptation engine (sections 13-15).

Pure business logic: no database access, no LLM calls. Given structured inputs it
produces plan constraints, a rule_trace explaining every decision, and a workout
plan draft. All thresholds live in app/rules/config.py.
"""

import datetime as dt
from dataclasses import dataclass, field

from app.config import settings
from app.core.enums import (
    ExperienceLevel,
    Intensity,
    MovementPattern,
    PrimaryGoal,
    WorkoutType,
)
from app.core.exceptions import AppError, ErrorCode
from app.rules.config import (
    FALLBACK_EXERCISE_COUNT,
    FALLBACK_INTENSITY,
    LOWER_BODY_MUSCLES,
    PAIN_RESTRICT_THRESHOLD,
    SLOTS_BY_TYPE,
    TIMED_EXERCISE_SECONDS,
    UPPER_BODY_MUSCLES,
)
from app.rules.duration import (
    ExerciseDraft,
    estimate_exercise_seconds,
    fit_duration,
    total_estimated_seconds,
)
from app.rules.exercise_filter import (
    ExerciseCandidate,
    FilterContext,
    filter_candidates,
    score_candidate,
)
from app.rules.intensity import select_intensity
from app.rules.progression import (
    rep_range_for_goal,
    rest_seconds_for,
    sets_for_experience,
    target_exercise_count,
    workout_type_for_goal,
)
from app.rules.recovery import compute_recovery_score
from app.rules.soreness import SorenessAnalysis, analyze_soreness


@dataclass
class EngineInputs:
    energy_score: int
    mood_score: int
    sleep_score: int
    stress_score: int
    pain_score: int | None
    soreness_map: dict[str, int]
    time_available_minutes: int | None
    primary_goal: str
    experience_level: str
    session_length_minutes: int
    equipment_slugs: list[str]
    recent_exercise_ids: set[str]
    last_session_exercise_ids: set[str]


@dataclass
class Constraints:
    recovery_score: float
    intensity: Intensity
    soreness: SorenessAnalysis
    time_budget_minutes: int
    workout_type: WorkoutType
    goal: PrimaryGoal
    experience_level: ExperienceLevel
    equipment_slugs: set[str]
    target_exercises: int
    recent_exercise_ids: set[str]
    last_session_exercise_ids: set[str]
    decision_facts: list[str] = field(default_factory=list)


@dataclass
class PlanDraft:
    workout_type: WorkoutType
    intensity: Intensity
    duration_minutes: int
    goal_tags: list[str]
    exercises: list[ExerciseDraft]


def build_constraints(inputs: EngineInputs) -> Constraints:
    """Compute plan constraints and raise a controlled error when safe generation is
    impossible under the configured rules (section 14.11)."""
    facts: list[str] = []

    if inputs.pain_score is not None and inputs.pain_score >= PAIN_RESTRICT_THRESHOLD:
        raise AppError(
            422,
            ErrorCode.WORKOUT_GENERATION_RESTRICTED,
            "Today's check-in contains recovery or pain values that prevent the normal "
            "workout generator from producing a suitable session.",
            {"suggested_action": "review_checkin"},
        )

    recovery_score = compute_recovery_score(
        inputs.energy_score,
        inputs.sleep_score,
        inputs.mood_score,
        inputs.stress_score,
        inputs.pain_score,
    )
    facts.append(f"Recovery score was {recovery_score}/10.")

    intensity = select_intensity(
        recovery_score, inputs.pain_score, inputs.sleep_score, inputs.stress_score
    )
    facts.append(f"Selected intensity was {intensity.value}.")

    soreness = analyze_soreness(inputs.soreness_map)
    if soreness.excluded_regions:
        facts.append(f"Highly sore regions: {', '.join(soreness.excluded_regions)}.")
    if soreness.deprioritized_regions:
        facts.append(f"Moderately sore regions: {', '.join(soreness.deprioritized_regions)}.")

    time_budget_minutes = inputs.time_available_minutes or inputs.session_length_minutes
    facts.append(f"Available time was {time_budget_minutes} minutes.")

    goal = PrimaryGoal(inputs.primary_goal)
    experience = ExperienceLevel(inputs.experience_level)
    workout_type = workout_type_for_goal(goal)
    facts.append(f"Primary goal was {goal.value}.")

    target_exercises = target_exercise_count(experience, time_budget_minutes)

    return Constraints(
        recovery_score=recovery_score,
        intensity=intensity,
        soreness=soreness,
        time_budget_minutes=time_budget_minutes,
        workout_type=workout_type,
        goal=goal,
        experience_level=experience,
        equipment_slugs=set(inputs.equipment_slugs),
        target_exercises=target_exercises,
        recent_exercise_ids=set(inputs.recent_exercise_ids),
        last_session_exercise_ids=set(inputs.last_session_exercise_ids),
        decision_facts=facts,
    )


def _filter_context(constraints: Constraints) -> FilterContext:
    return FilterContext(
        equipment_slugs=constraints.equipment_slugs,
        experience_level=constraints.experience_level,
        excluded_muscles=constraints.soreness.excluded_muscles,
        deprioritized_muscles=constraints.soreness.deprioritized_muscles,
        recent_exercise_ids=constraints.recent_exercise_ids,
        last_session_exercise_ids=constraints.last_session_exercise_ids,
    )


def _pick_best(
    candidates: list[ExerciseCandidate],
    context: FilterContext,
    chosen_ids: set[str],
) -> ExerciseCandidate | None:
    candidates = filter_candidates(candidates, context)
    scored = sorted(
        ((score_candidate(ex, context), ex.slug, ex) for ex in candidates),
        key=lambda item: (-item[0], item[1]),
    )
    for _, _, ex in scored:
        if ex.id not in chosen_ids:
            return ex
    return None


def build_plan(constraints: Constraints, catalog: list[ExerciseCandidate]) -> PlanDraft:
    """Deterministic, slot-based plan builder (sections 14.4-14.9)."""
    context = _filter_context(constraints)
    slots = SLOTS_BY_TYPE[constraints.workout_type]
    chosen: list[ExerciseCandidate] = []
    chosen_ids: set[str] = set()

    for slot in slots:
        if len(chosen) >= constraints.target_exercises:
            break
        candidates = [ex for ex in catalog if ex.movement_pattern == slot]
        picked = _pick_best(candidates, context, chosen_ids)
        if picked:
            chosen.append(picked)
            chosen_ids.add(picked.id)

    if len(chosen) < constraints.target_exercises:
        from app.rules.config import FILL_PATTERNS

        if constraints.workout_type == WorkoutType.MOBILITY:
            # Mobility sessions stay movement/mobility based.
            fill_slots = [
                MovementPattern.CORE,
                MovementPattern.CARDIO,
                MovementPattern.MOBILITY,
            ]
        else:
            fill_slots = FILL_PATTERNS
        for pattern in fill_slots:
            if len(chosen) >= constraints.target_exercises:
                break
            if pattern in slots:
                continue
            candidates = [ex for ex in catalog if ex.movement_pattern == pattern]
            picked = _pick_best(candidates, context, chosen_ids)
            if picked:
                chosen.append(picked)
                chosen_ids.add(picked.id)

    if not chosen:
        raise AppError(
            422,
            ErrorCode.WORKOUT_GENERATION_RESTRICTED,
            "The available equipment and recovery constraints prevent a safe workout plan.",
            {"suggested_action": "review_checkin"},
        )
    return _finalize(chosen, constraints)


def _finalize(chosen: list[ExerciseCandidate], constraints: Constraints) -> PlanDraft:
    drafts: list[ExerciseDraft] = []
    for position, ex in enumerate(chosen, start=1):
        drafts.append(_prescribe(ex, constraints, position))

    budget_seconds = constraints.time_budget_minutes * 60
    if total_estimated_seconds(drafts) > budget_seconds:
        drafts = fit_duration(drafts, budget_seconds)
    if not drafts:
        raise AppError(
            422,
            ErrorCode.WORKOUT_GENERATION_RESTRICTED,
            "The available time and recovery constraints prevent a safe workout plan.",
            {"suggested_action": "review_checkin"},
        )
    return PlanDraft(
        workout_type=constraints.workout_type,
        intensity=constraints.intensity,
        duration_minutes=constraints.time_budget_minutes,
        goal_tags=[constraints.goal.value, _focus_tag(constraints)],
        exercises=drafts,
    )


def _focus_tag(constraints: Constraints) -> str:
    if constraints.workout_type == WorkoutType.MOBILITY:
        return "mobility"
    excluded = constraints.soreness.excluded_muscles
    lower_blocked = bool(excluded & LOWER_BODY_MUSCLES)
    upper_blocked = bool(excluded & UPPER_BODY_MUSCLES)
    if lower_blocked and not upper_blocked:
        return "upper_body"
    if upper_blocked and not lower_blocked:
        return "lower_body"
    return "full_body"


def _prescribe(ex: ExerciseCandidate, constraints: Constraints, position: int) -> ExerciseDraft:
    tags: list[str] = []
    if ex.is_timed:
        sets = None
        reps_min = reps_max = None
        duration_seconds = TIMED_EXERCISE_SECONDS.get(ex.workout_type.value, 45)
        rest_seconds = None
        tags = ["timed", ex.workout_type.value]
        estimated = estimate_exercise_seconds(None, None, duration_seconds)
    else:
        sets = sets_for_experience(constraints.experience_level, constraints.intensity)
        reps = rep_range_for_goal(constraints.goal)
        reps_min, reps_max = reps if reps else (None, None)
        rest_seconds = rest_seconds_for(constraints.goal, ex.default_rest_seconds, is_timed=False)
        duration_seconds = None
        if constraints.intensity == Intensity.LOW:
            tags.append("reduced_sets")
        estimated = estimate_exercise_seconds(sets, rest_seconds, None)
    return ExerciseDraft(
        exercise_id=ex.id,
        slug=ex.slug,
        name=ex.name,
        position=position,
        sets=sets,
        reps_min=reps_min,
        reps_max=reps_max,
        duration_seconds=duration_seconds,
        rest_seconds=rest_seconds,
        adaptation_tags=tags,
        estimated_seconds=estimated,
    )


def build_fallback_plan(constraints: Constraints, catalog: list[ExerciseCandidate]) -> PlanDraft:
    """Simplified bodyweight-only fallback (section 15)."""
    fallback_constraints = Constraints(
        recovery_score=constraints.recovery_score,
        intensity=FALLBACK_INTENSITY,
        soreness=constraints.soreness,
        time_budget_minutes=constraints.time_budget_minutes,
        workout_type=WorkoutType.MOBILITY,
        goal=constraints.goal,
        experience_level=constraints.experience_level,
        equipment_slugs=constraints.equipment_slugs,
        target_exercises=FALLBACK_EXERCISE_COUNT,
        recent_exercise_ids=constraints.recent_exercise_ids,
        last_session_exercise_ids=constraints.last_session_exercise_ids,
    )
    context = _filter_context(fallback_constraints)
    chosen: list[ExerciseCandidate] = []
    chosen_ids: set[str] = set()
    candidates = [
        ex
        for ex in catalog
        if ex.workout_type in (WorkoutType.CARDIO, WorkoutType.MOBILITY)
        or ex.movement_pattern == "core"
    ]
    picked = _pick_best(candidates, context, chosen_ids)
    while picked and len(chosen) < FALLBACK_EXERCISE_COUNT:
        chosen.append(picked)
        chosen_ids.add(picked.id)
        picked = _pick_best(candidates, context, chosen_ids)
    if not chosen:
        raise AppError(
            422,
            ErrorCode.WORKOUT_VALIDATION_FAILED,
            "The workout generator could not produce a valid plan.",
            {"suggested_action": "review_checkin"},
        )
    return _finalize(chosen, fallback_constraints)


def build_rule_trace(
    constraints: Constraints,
    draft: PlanDraft,
    inputs: EngineInputs,
    checkin_date: dt.date,
) -> dict:
    """Canonical structured truth used for explanations (Appendix D)."""
    return {
        "version": settings.generator_version,
        "checkin_date": checkin_date.isoformat(),
        "recovery": {
            "score": constraints.recovery_score,
            "energy": inputs.energy_score,
            "sleep": inputs.sleep_score,
            "mood": inputs.mood_score,
            "stress": inputs.stress_score,
            "pain": inputs.pain_score,
        },
        "soreness": {
            "excluded_regions": constraints.soreness.excluded_regions,
            "deprioritized_regions": constraints.soreness.deprioritized_regions,
        },
        "constraints": {
            "time_available_minutes": constraints.time_budget_minutes,
            "equipment_slugs": sorted(constraints.equipment_slugs),
            "experience_level": constraints.experience_level.value,
            "primary_goal": constraints.goal.value,
        },
        "decisions": {
            "intensity": draft.intensity.value,
            "workout_type": draft.workout_type.value,
            "focus": draft.goal_tags,
        },
        "decision_facts": constraints.decision_facts,
    }
