"""Check-in services (section 12)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dates import local_date
from app.core.exceptions import AppError, ErrorCode
from app.db.models.checkin import CheckIn
from app.repositories.checkins import CheckInRepository
from app.schemas.checkin import CANONICAL_REGIONS, CheckInCreate, CheckInUpdate


def validate_soreness_map(soreness_map: dict[str, int]) -> None:
    for region, score in soreness_map.items():
        if region not in CANONICAL_REGIONS:
            raise AppError(
                422,
                ErrorCode.CHECKIN_INVALID,
                f"Unknown body region: {region}.",
                {"valid_regions": sorted(CANONICAL_REGIONS)},
            )
        if not 1 <= score <= 10:
            raise AppError(
                422,
                ErrorCode.CHECKIN_INVALID,
                f"Soreness score for {region} must be between 1 and 10.",
            )


async def create_check_in(
    session: AsyncSession,
    user_id: uuid.UUID,
    payload: CheckInCreate,
    tz_name: str,
) -> CheckIn:
    repo = CheckInRepository(session)
    validate_soreness_map(payload.soreness_map)
    today = local_date(tz_name)
    existing = await repo.get_for_date(user_id, today)
    if existing is not None:
        raise AppError(
            409,
            ErrorCode.CHECKIN_ALREADY_EXISTS,
            "A check-in already exists for today. Use PUT to update it.",
        )
    check_in = await repo.create(
        user_id,
        today,
        payload.model_dump(),
    )
    await session.commit()
    return check_in


async def update_check_in(
    session: AsyncSession,
    user_id: uuid.UUID,
    check_in_id: uuid.UUID,
    payload: CheckInUpdate,
    tz_name: str,
) -> CheckIn:
    repo = CheckInRepository(session)
    check_in = await repo.get(user_id, check_in_id)
    if check_in is None:
        raise AppError(404, ErrorCode.CHECKIN_NOT_FOUND, "The requested check-in was not found.")
    if check_in.checkin_date != local_date(tz_name):
        raise AppError(
            422,
            ErrorCode.CHECKIN_INVALID,
            "Only today's check-in can be edited.",
        )
    changes = payload.model_dump(exclude_unset=True)
    if "soreness_map" in changes:
        if changes["soreness_map"] is None:
            raise AppError(
                422,
                ErrorCode.CHECKIN_INVALID,
                "Soreness map cannot be null; send an empty object when nothing is sore.",
            )
        validate_soreness_map(changes["soreness_map"])
    for key, value in changes.items():
        setattr(check_in, key, value)
    await session.flush()
    await session.commit()
    return check_in


async def get_check_in(
    session: AsyncSession, user_id: uuid.UUID, check_in_id: uuid.UUID
) -> CheckIn:
    repo = CheckInRepository(session)
    check_in = await repo.get(user_id, check_in_id)
    if check_in is None:
        raise AppError(404, ErrorCode.CHECKIN_NOT_FOUND, "The requested check-in was not found.")
    return check_in


async def get_today_check_in(
    session: AsyncSession, user_id: uuid.UUID, tz_name: str
) -> CheckIn | None:
    repo = CheckInRepository(session)
    return await repo.get_for_date(user_id, local_date(tz_name))


async def list_check_ins(
    session: AsyncSession, user_id: uuid.UUID, page: int, page_size: int
) -> tuple[list[CheckIn], int]:
    repo = CheckInRepository(session)
    return await repo.paginate(user_id, page, page_size)
