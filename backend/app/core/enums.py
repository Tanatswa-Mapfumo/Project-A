"""Centralized domain enums (Appendix A of the build spec)."""

from enum import StrEnum


class PrimaryGoal(StrEnum):
    LOSE_FAT = "lose_fat"
    GAIN_MUSCLE = "gain_muscle"
    GET_STRONGER = "get_stronger"
    IMPROVE_MOBILITY = "improve_mobility"


class ExperienceLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class WorkoutType(StrEnum):
    STRENGTH = "strength"
    CARDIO = "cardio"
    MOBILITY = "mobility"
    MIXED = "mixed"


class Intensity(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class WorkoutStatus(StrEnum):
    GENERATED = "generated"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SessionStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    QUIT = "quit"


class Difficulty(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class MovementPattern(StrEnum):
    SQUAT = "squat"
    HINGE = "hinge"
    HORIZONTAL_PUSH = "horizontal_push"
    VERTICAL_PUSH = "vertical_push"
    HORIZONTAL_PULL = "horizontal_pull"
    VERTICAL_PULL = "vertical_pull"
    CARRY = "carry"
    CORE = "core"
    CARDIO = "cardio"
    MOBILITY = "mobility"


class Weekday(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class TrendDirection(StrEnum):
    UP = "up"
    STABLE = "stable"
    DOWN = "down"
    INSUFFICIENT_DATA = "insufficient_data"


class VolumeDirection(StrEnum):
    UP = "up"
    MAINTAIN = "maintain"
    DOWN = "down"
