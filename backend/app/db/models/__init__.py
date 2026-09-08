"""Import all models so Alembic and metadata.create_all see them."""

from app.db.models.catalog import Equipment, Exercise, ExerciseEquipment, UserEquipment
from app.db.models.checkin import CheckIn
from app.db.models.profile import (
    AccessibilityProfile,
    AuthUser,
    GoalProfile,
    NotificationPreferences,
    Profile,
    TrainingProfile,
)
from app.db.models.session import WorkoutSession
from app.db.models.weekly import WeeklySummary
from app.db.models.workout import WorkoutExercise, WorkoutExplanation, WorkoutPlan

__all__ = [
    "AccessibilityProfile",
    "AuthUser",
    "CheckIn",
    "Equipment",
    "Exercise",
    "ExerciseEquipment",
    "GoalProfile",
    "NotificationPreferences",
    "Profile",
    "TrainingProfile",
    "UserEquipment",
    "WeeklySummary",
    "WorkoutExplanation",
    "WorkoutExercise",
    "WorkoutPlan",
    "WorkoutSession",
]
