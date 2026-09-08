"""Profile / onboarding endpoints (section 10)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.exceptions import AppError, ErrorCode
from app.db.session import get_db
from app.repositories.profiles import (
    AccessibilityRepository,
    EquipmentRepository,
    GoalsRepository,
    NotificationRepository,
    ProfileRepository,
    TrainingProfileRepository,
)
from app.schemas.profile import (
    AccessibilityIn,
    AccessibilityOut,
    EquipmentIn,
    EquipmentOut,
    GoalsIn,
    GoalsOut,
    NotificationsIn,
    NotificationsOut,
    OnboardingCompleteOut,
    ProfileOut,
    ProfileUpdate,
    TrainingProfileIn,
    TrainingProfileOut,
)
from app.services import onboarding

router = APIRouter(prefix="/me", tags=["Profile"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
User = Annotated[CurrentUser, Depends(get_current_user)]


async def _require_profile(session: AsyncSession, user_id: uuid.UUID):
    profile = await ProfileRepository(session).get(user_id)
    if profile is None:
        raise AppError(404, ErrorCode.PROFILE_NOT_FOUND, "The profile was not found.")
    return profile


@router.get(
    "",
    response_model=ProfileOut,
    summary="Get my profile",
    description="Returns the authenticated user's profile.",
)
async def get_me(session: DbSession, user: User):
    return await _require_profile(session, uuid.UUID(user.profile_id))


@router.patch(
    "",
    response_model=ProfileOut,
    summary="Update my profile",
    description="Partially updates name, age, height, weight, gender, country, or timezone. "
    "Identity fields cannot be changed.",
)
async def patch_me(body: ProfileUpdate, session: DbSession, user: User):
    profile = await _require_profile(session, uuid.UUID(user.profile_id))
    return await onboarding.patch_profile(session, profile, body.model_dump(exclude_unset=True))


@router.get(
    "/goals",
    response_model=GoalsOut,
    summary="Get my goals",
    description="Returns the authenticated user's persisted goal profile.",
    responses={404: {"description": "Goals have not been set."}},
)
async def get_goals(session: DbSession, user: User):
    goal = await GoalsRepository(session).get(uuid.UUID(user.profile_id))
    if goal is None:
        raise AppError(404, ErrorCode.PROFILE_NOT_FOUND, "Goals have not been set yet.")
    return goal


@router.put(
    "/goals",
    response_model=GoalsOut,
    summary="Set my goals",
    description="Upserts the primary and secondary goal plus target metrics.",
)
async def put_goals(body: GoalsIn, session: DbSession, user: User):
    return await onboarding.upsert_goals(
        session,
        uuid.UUID(user.profile_id),
        body.primary_goal,
        body.secondary_goal,
        body.target_metrics,
    )


@router.get(
    "/training-profile",
    response_model=TrainingProfileOut,
    summary="Get my training profile",
    description="Returns experience level, preferred training days, and session length.",
    responses={404: {"description": "Training profile has not been set."}},
)
async def get_training_profile(session: DbSession, user: User):
    training = await TrainingProfileRepository(session).get(uuid.UUID(user.profile_id))
    if training is None:
        raise AppError(404, ErrorCode.PROFILE_NOT_FOUND, "Training profile has not been set yet.")
    return training


@router.put(
    "/training-profile",
    response_model=TrainingProfileOut,
    summary="Set my training profile",
    description="Upserts experience level, preferred days, and session length.",
)
async def put_training_profile(body: TrainingProfileIn, session: DbSession, user: User):
    return await onboarding.upsert_training_profile(
        session,
        uuid.UUID(user.profile_id),
        body.experience_level,
        list(body.preferred_days),
        body.session_length_minutes,
    )


@router.get(
    "/accessibility",
    response_model=AccessibilityOut,
    summary="Get my accessibility preferences",
    description="Returns the six persisted accessibility toggles for this user.",
    responses={404: {"description": "Accessibility profile has not been set."}},
)
async def get_accessibility(session: DbSession, user: User):
    accessibility = await AccessibilityRepository(session).get(uuid.UUID(user.profile_id))
    if accessibility is None:
        raise AppError(
            404, ErrorCode.PROFILE_NOT_FOUND, "Accessibility profile has not been set yet."
        )
    return accessibility


@router.put(
    "/accessibility",
    response_model=AccessibilityOut,
    summary="Set my accessibility preferences",
    description="Persists the six accessibility toggles immediately.",
)
async def put_accessibility(body: AccessibilityIn, session: DbSession, user: User):
    return await onboarding.upsert_accessibility(
        session, uuid.UUID(user.profile_id), body.model_dump()
    )


@router.get(
    "/equipment",
    response_model=EquipmentOut,
    summary="Get my equipment",
    description="Returns the equipment ids the user owns (empty list if none).",
)
async def get_equipment(session: DbSession, user: User):
    ids = await EquipmentRepository(session).get_ids_for_user(uuid.UUID(user.profile_id))
    return EquipmentOut(equipment_ids=ids)


@router.put(
    "/equipment",
    response_model=EquipmentOut,
    summary="Set my equipment",
    description="Transactionally replaces the user's equipment set.",
)
async def put_equipment(body: EquipmentIn, session: DbSession, user: User):
    return EquipmentOut(
        equipment_ids=(
            await onboarding.replace_equipment(
                session, uuid.UUID(user.profile_id), body.equipment_ids
            )
        )["equipment_ids"]
    )


@router.get(
    "/notifications",
    response_model=NotificationsOut,
    summary="Get my notification preferences",
    description=(
        "Returns persisted notification preferences, creating default preferences if absent."
    ),
)
async def get_notifications(session: DbSession, user: User):
    prefs = await NotificationRepository(session).get(uuid.UUID(user.profile_id))
    if prefs is None:
        prefs = await NotificationRepository(session).upsert(uuid.UUID(user.profile_id), {})
        await session.commit()
    return prefs


@router.put(
    "/notifications",
    response_model=NotificationsOut,
    summary="Set my notification preferences",
    description="Persists notification toggles (delivery is out of scope for the POC).",
)
async def put_notifications(body: NotificationsIn, session: DbSession, user: User):
    return await onboarding.upsert_notifications(
        session, uuid.UUID(user.profile_id), body.model_dump()
    )


@router.post(
    "/onboarding/complete",
    response_model=OnboardingCompleteOut,
    summary="Complete onboarding",
    description="Validates that profile basics, goals, training profile, accessibility "
    "profile, and a baseline check-in exist, then sets `onboarding_completed`.",
    responses={422: {"description": "Required onboarding components are missing."}},
)
async def complete_onboarding(session: DbSession, user: User):
    await onboarding.complete_onboarding(session, uuid.UUID(user.profile_id))
    return OnboardingCompleteOut()
