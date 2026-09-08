"""Onboarding and profile services (section 10)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, ErrorCode
from app.db.models.profile import Profile
from app.repositories.checkins import CheckInRepository
from app.repositories.profiles import (
    AccessibilityRepository,
    EquipmentRepository,
    GoalsRepository,
    NotificationRepository,
    ProfileRepository,
    TrainingProfileRepository,
)


async def patch_profile(session: AsyncSession, profile: Profile, values: dict) -> Profile:
    for key, value in values.items():
        if value is not None:
            setattr(profile, key, value)
    await session.flush()
    await session.commit()
    return profile


async def upsert_goals(
    session: AsyncSession,
    user_id: uuid.UUID,
    primary_goal: str,
    secondary_goal: str | None,
    target_metrics: dict,
):
    repo = GoalsRepository(session)
    goal = await repo.upsert(user_id, primary_goal, secondary_goal, target_metrics)
    await session.commit()
    return goal


async def upsert_training_profile(
    session: AsyncSession,
    user_id: uuid.UUID,
    experience_level: str,
    preferred_days: list[str],
    session_length_minutes: int,
):
    repo = TrainingProfileRepository(session)
    training = await repo.upsert(user_id, experience_level, preferred_days, session_length_minutes)
    await session.commit()
    return training


async def upsert_accessibility(session: AsyncSession, user_id: uuid.UUID, values: dict):
    repo = AccessibilityRepository(session)
    accessibility = await repo.upsert(user_id, values)
    await session.commit()
    return accessibility


async def replace_equipment(
    session: AsyncSession, user_id: uuid.UUID, equipment_ids: list[uuid.UUID]
):
    repo = EquipmentRepository(session)
    for equipment_id in equipment_ids:
        if not await repo.exists(equipment_id):
            raise AppError(
                404,
                ErrorCode.EQUIPMENT_NOT_FOUND,
                f"Equipment {equipment_id} does not exist.",
            )
    await repo.replace_for_user(user_id, equipment_ids)
    await session.commit()
    return {"equipment_ids": equipment_ids}


async def upsert_notifications(session: AsyncSession, user_id: uuid.UUID, values: dict):
    repo = NotificationRepository(session)
    prefs = await repo.upsert(user_id, values)
    await session.commit()
    return prefs


async def complete_onboarding(session: AsyncSession, user_id: uuid.UUID) -> Profile:
    profile_repo = ProfileRepository(session)
    goals_repo = GoalsRepository(session)
    training_repo = TrainingProfileRepository(session)
    accessibility_repo = AccessibilityRepository(session)
    checkin_repo = CheckInRepository(session)

    profile = await profile_repo.get(user_id)
    if profile is None:
        raise AppError(404, ErrorCode.PROFILE_NOT_FOUND, "The profile was not found.")

    missing: list[str] = []
    if not all([profile.name, profile.age, profile.height_cm, profile.weight_kg]):
        missing.append("profile_basics")
    if await goals_repo.get(user_id) is None:
        missing.append("goals")
    if await training_repo.get(user_id) is None:
        missing.append("training_profile")
    if await accessibility_repo.get(user_id) is None:
        missing.append("accessibility")
    if await checkin_repo.count_for_user(user_id) == 0:
        missing.append("baseline_checkin")

    if missing:
        raise AppError(
            422,
            ErrorCode.ONBOARDING_INCOMPLETE,
            "Onboarding cannot be completed because required components are missing.",
            {"missing": missing},
        )
    profile.onboarding_completed = True
    await session.commit()
    return profile
