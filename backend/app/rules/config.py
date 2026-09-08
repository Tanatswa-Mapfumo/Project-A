"""Single source of truth for all deterministic rule constants.

All thresholds used by the adaptation engine live here so they can be tuned without
scattering magic numbers through the codebase.
"""

from app.core.enums import (
    ExperienceLevel,
    Intensity,
    MovementPattern,
    PrimaryGoal,
    WorkoutType,
)

GENERATOR_VERSION = "rules-v1"

# --- Recovery score weights (section 14.1) ---
RECOVERY_WEIGHTS = {
    "energy": 0.30,
    "sleep": 0.25,
    "mood": 0.15,
    "stress": 0.20,
    "pain": 0.10,
}

# --- Intensity selection (section 14.2) ---
INTENSITY_LOW_THRESHOLD = 4.5
INTENSITY_HIGH_THRESHOLD = 7.0
PAIN_INTENSITY_CAP = 6
SLEEP_INTENSITY_CAP = 3
STRESS_INTENSITY_CAP = 9

# --- Soreness bands (section 14.3) ---
SORENESS_DEPRIORITIZE_MIN = 4
SORENESS_EXCLUDE_MIN = 7

# --- Safety (section 14.11) ---
PAIN_RESTRICT_THRESHOLD = 8

# --- Body region -> muscle group mapping (section 14.3, Appendix B) ---
# Joint regions (knees/ankles/hips) conservatively affect the related muscles.
BODY_REGION_TO_MUSCLES: dict[str, list[str]] = {
    "chest": ["chest"],
    "shoulders": ["front_delts", "side_delts", "rear_delts"],
    "upper_back": ["lats", "traps", "rhomboids"],
    "lower_back": ["erectors"],
    "biceps": ["biceps"],
    "triceps": ["triceps"],
    "forearms": ["forearms"],
    "core": ["core"],
    "glutes": ["glutes"],
    "quads": ["quadriceps"],
    "hamstrings": ["hamstrings"],
    "calves": ["calves"],
    "hips": ["hip_flexors", "glutes"],
    "knees": ["quadriceps", "hamstrings", "calves"],
    "ankles": ["calves"],
}

LOWER_BODY_MUSCLES = {"quadriceps", "hamstrings", "glutes", "calves", "hip_flexors"}
UPPER_BODY_MUSCLES = {
    "chest",
    "front_delts",
    "side_delts",
    "rear_delts",
    "biceps",
    "triceps",
    "forearms",
    "lats",
    "traps",
    "rhomboids",
    "erectors",
}

# --- Goal templates (section 14.4) ---
GOAL_WORKOUT_TYPE: dict[PrimaryGoal, WorkoutType] = {
    PrimaryGoal.LOSE_FAT: WorkoutType.MIXED,
    PrimaryGoal.GAIN_MUSCLE: WorkoutType.STRENGTH,
    PrimaryGoal.GET_STRONGER: WorkoutType.STRENGTH,
    PrimaryGoal.IMPROVE_MOBILITY: WorkoutType.MOBILITY,
}

GOAL_REP_RANGES: dict[PrimaryGoal, tuple[int, int] | None] = {
    PrimaryGoal.LOSE_FAT: (8, 15),
    PrimaryGoal.GAIN_MUSCLE: (8, 12),
    PrimaryGoal.GET_STRONGER: (4, 8),
    PrimaryGoal.IMPROVE_MOBILITY: None,
}

STRONGER_MIN_REST_SECONDS = 120

# --- Experience volume (section 14.5) ---
EXPERIENCE_SETS: dict[ExperienceLevel, int] = {
    ExperienceLevel.BEGINNER: 2,
    ExperienceLevel.INTERMEDIATE: 3,
    ExperienceLevel.ADVANCED: 4,
}

EXPERIENCE_EXERCISE_COUNT: dict[ExperienceLevel, int] = {
    ExperienceLevel.BEGINNER: 5,
    ExperienceLevel.INTERMEDIATE: 6,
    ExperienceLevel.ADVANCED: 7,
}

# Duration scaling reference: counts above are for a 45-minute session.
REFERENCE_DURATION_MINUTES = 45
MAX_EXERCISES = 8
MIN_EXERCISES = 1

# --- Duration estimation (section 14.6) ---
SET_TIME_SECONDS = 40  # conservative per-set work + setup time
TRANSITION_SECONDS = 45  # change-over allowance per exercise
TIMED_EXERCISE_SECONDS: dict[str, int] = {"cardio": 60, "mobility": 45}
STRENGTH_FALLBACK_REST_SECONDS = 60

# --- Movement balance slot templates (section 14.8) ---
SLOTS_BY_TYPE: dict[WorkoutType, list[MovementPattern]] = {
    WorkoutType.STRENGTH: [
        MovementPattern.SQUAT,
        MovementPattern.HINGE,
        MovementPattern.HORIZONTAL_PUSH,
        MovementPattern.VERTICAL_PUSH,
        MovementPattern.HORIZONTAL_PULL,
        MovementPattern.VERTICAL_PULL,
        MovementPattern.CORE,
    ],
    WorkoutType.MIXED: [
        MovementPattern.SQUAT,
        MovementPattern.HINGE,
        MovementPattern.HORIZONTAL_PUSH,
        MovementPattern.HORIZONTAL_PULL,
        MovementPattern.CARDIO,
        MovementPattern.CORE,
    ],
    WorkoutType.MOBILITY: [
        MovementPattern.MOBILITY,
        MovementPattern.MOBILITY,
        MovementPattern.MOBILITY,
        MovementPattern.CORE,
        MovementPattern.MOBILITY,
        MovementPattern.MOBILITY,
    ],
    WorkoutType.CARDIO: [MovementPattern.CARDIO, MovementPattern.CORE],
}

FILL_PATTERNS: list[MovementPattern] = [
    MovementPattern.CORE,
    MovementPattern.CARDIO,
    MovementPattern.MOBILITY,
    MovementPattern.SQUAT,
    MovementPattern.HINGE,
    MovementPattern.HORIZONTAL_PUSH,
    MovementPattern.VERTICAL_PUSH,
    MovementPattern.HORIZONTAL_PULL,
    MovementPattern.VERTICAL_PULL,
    MovementPattern.CARRY,
]

# --- Scoring (section 14.9) ---
SCORE_DEPRIORITIZED_MUSCLE = -10
SCORE_LAST_SESSION_REUSE = -2
SCORE_RECENT_REUSE = -1
SCORE_FRESH_EXERCISE = 1

# --- Difficulty bounds by experience ---
DIFFICULTY_RANK = {"beginner": 0, "intermediate": 1, "advanced": 2}
MAX_DIFFICULTY_BY_EXPERIENCE: dict[ExperienceLevel, int] = {
    ExperienceLevel.BEGINNER: 0,
    ExperienceLevel.INTERMEDIATE: 1,
    ExperienceLevel.ADVANCED: 2,
}

# --- Bodyweight is always available (section 14.7) ---
UNIVERSAL_EQUIPMENT_SLUGS = {"bodyweight"}

# --- History lookback (section 14.9) ---
HISTORY_LOOKBACK_SESSIONS = 3

# --- Weekly / progress ---
CONSISTENCY_WINDOW_DAYS = 7
TREND_CHANGE_THRESHOLD_PERCENT = 5.0

# --- Fallback plan (section 15) ---
FALLBACK_EXERCISE_COUNT = 2
FALLBACK_INTENSITY = Intensity.LOW

# --- LLM output validation ---
SHORT_EXPLANATION_MAX_CHARS = 500
BANNED_MEDICAL_TERMS = [
    "diagnos",
    "injur",
    "disease",
    "medical",
    "physiotherap",
    "doctor",
    "prescrib",
    "treatment",
    "condition",
    "suffer",
]
