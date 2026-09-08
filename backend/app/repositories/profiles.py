"""Profile, goal, training, accessibility, equipment, and notification repositories.

Ownership filter: every personal-resource query includes the user's profile id
(section 43: Data Ownership Pattern).
"""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import Equipment, UserEquipment
from app.db.models.profile import (
    AccessibilityProfile,
    AuthUser,
    GoalProfile,
    NotificationPreferences,
    Profile,
    TrainingProfile,
)


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID) -> Profile | None:
        return await self.session.get(Profile, user_id)

    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> Profile | None:
        result = await self.session.execute(
            select(Profile).where(Profile.auth_user_id == auth_user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Profile | None:
        result = await self.session.execute(select(Profile).where(Profile.email == email))
        return result.scalar_one_or_none()

    async def create(self, auth_user_id: uuid.UUID, email: str) -> Profile:
        profile = Profile(auth_user_id=auth_user_id, email=email)
        self.session.add(profile)
        await self.session.flush()
        await self._create_default_notifications(profile.id)
        return profile

    async def _create_default_notifications(self, user_id: uuid.UUID) -> None:
        self.session.add(NotificationPreferences(user_id=user_id))

    async def get_auth_user_by_email(self, email: str) -> AuthUser | None:
        result = await self.session.execute(select(AuthUser).where(AuthUser.email == email))
        return result.scalar_one_or_none()

    async def create_auth_user(self, email: str, password_hash: str | None) -> AuthUser:
        auth_user = AuthUser(email=email, password_hash=password_hash)
        self.session.add(auth_user)
        await self.session.flush()
        return auth_user


class GoalsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID) -> GoalProfile | None:
        result = await self.session.execute(
            select(GoalProfile).where(GoalProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        user_id: uuid.UUID,
        primary_goal: str,
        secondary_goal: str | None,
        target_metrics: dict,
    ) -> GoalProfile:
        goal = await self.get(user_id)
        if goal is None:
            goal = GoalProfile(
                user_id=user_id,
                primary_goal=primary_goal,
                secondary_goal=secondary_goal,
                target_metrics=target_metrics,
            )
            self.session.add(goal)
        else:
            goal.primary_goal = primary_goal
            goal.secondary_goal = secondary_goal
            goal.target_metrics = target_metrics
        await self.session.flush()
        return goal


class TrainingProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID) -> TrainingProfile | None:
        result = await self.session.execute(
            select(TrainingProfile).where(TrainingProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        user_id: uuid.UUID,
        experience_level: str,
        preferred_days: list[str],
        session_length_minutes: int,
    ) -> TrainingProfile:
        training = await self.get(user_id)
        if training is None:
            training = TrainingProfile(
                user_id=user_id,
                experience_level=experience_level,
                preferred_days=preferred_days,
                session_length_minutes=session_length_minutes,
            )
            self.session.add(training)
        else:
            training.experience_level = experience_level
            training.preferred_days = preferred_days
            training.session_length_minutes = session_length_minutes
        await self.session.flush()
        return training


class AccessibilityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID) -> AccessibilityProfile | None:
        result = await self.session.execute(
            select(AccessibilityProfile).where(AccessibilityProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: uuid.UUID, values: dict) -> AccessibilityProfile:
        accessibility = await self.get(user_id)
        if accessibility is None:
            accessibility = AccessibilityProfile(user_id=user_id, **values)
            self.session.add(accessibility)
        else:
            for key, value in values.items():
                setattr(accessibility, key, value)
        await self.session.flush()
        return accessibility


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID) -> NotificationPreferences | None:
        result = await self.session.execute(
            select(NotificationPreferences).where(NotificationPreferences.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: uuid.UUID, values: dict) -> NotificationPreferences:
        prefs = await self.get(user_id)
        if prefs is None:
            prefs = NotificationPreferences(user_id=user_id, **values)
            self.session.add(prefs)
        else:
            for key, value in values.items():
                setattr(prefs, key, value)
        await self.session.flush()
        return prefs


class EquipmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_ids_for_user(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self.session.execute(
            select(UserEquipment.equipment_id).where(UserEquipment.user_id == user_id)
        )
        return list(result.scalars().all())

    async def replace_for_user(self, user_id: uuid.UUID, equipment_ids: list[uuid.UUID]) -> None:
        await self.session.execute(delete(UserEquipment).where(UserEquipment.user_id == user_id))
        for equipment_id in equipment_ids:
            self.session.add(UserEquipment(user_id=user_id, equipment_id=equipment_id))
        await self.session.flush()

    async def exists(self, equipment_id: uuid.UUID) -> bool:
        equipment = await self.session.get(Equipment, equipment_id)
        return equipment is not None
