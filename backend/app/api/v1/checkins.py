"""Daily check-in endpoints (section 12)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TzName
from app.core.auth import CurrentUser, get_current_user
from app.core.exceptions import AppError, ErrorCode
from app.db.session import get_db
from app.schemas.checkin import CheckInCreate, CheckInOut, CheckInUpdate
from app.schemas.common import Page, PageParams
from app.services import checkins

router = APIRouter(prefix="/check-ins", tags=["Check-Ins"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
User = Annotated[CurrentUser, Depends(get_current_user)]
PageQuery = Annotated[PageParams, Depends()]


@router.post(
    "",
    response_model=CheckInOut,
    status_code=201,
    summary="Create today's check-in",
    description="Stores the daily recovery check-in for the user's local calendar day. "
    "One check-in per user per day; a second POST returns 409.",
    responses={
        409: {"description": "A check-in already exists for today."},
        422: {"description": "Invalid scores or region keys."},
    },
)
async def create_check_in(body: CheckInCreate, session: DbSession, user: User, tz: TzName):
    return await checkins.create_check_in(session, uuid.UUID(user.profile_id), body, tz)


@router.get(
    "/today",
    response_model=CheckInOut,
    summary="Get today's check-in",
    description="Returns the check-in for the user's current local calendar day.",
    responses={404: {"description": "No check-in yet today."}},
)
async def get_today_check_in(session: DbSession, user: User, tz: TzName):
    check_in = await checkins.get_today_check_in(session, uuid.UUID(user.profile_id), tz)
    if check_in is None:
        raise AppError(404, ErrorCode.CHECKIN_NOT_FOUND, "No check-in exists for today.")
    return check_in


@router.get(
    "",
    response_model=Page[CheckInOut],
    summary="List my check-ins",
    description="Paginated check-in history, newest first.",
)
async def list_check_ins(session: DbSession, user: User, params: PageQuery):
    items, total = await checkins.list_check_ins(
        session, uuid.UUID(user.profile_id), params.page, params.page_size
    )
    return Page(items=items, page=params.page, page_size=params.page_size, total=total)


@router.get(
    "/{check_in_id}",
    response_model=CheckInOut,
    summary="Get a check-in",
    description="Returns one check-in owned by the authenticated user.",
    responses={404: {"description": "Check-in not found."}},
)
async def get_check_in(check_in_id: uuid.UUID, session: DbSession, user: User):
    return await checkins.get_check_in(session, uuid.UUID(user.profile_id), check_in_id)


@router.put(
    "/{check_in_id}",
    response_model=CheckInOut,
    summary="Edit today's check-in",
    description="Updates fields of today's check-in only.",
    responses={
        404: {"description": "Check-in not found."},
        422: {"description": "Check-in is not from today."},
    },
)
async def update_check_in(
    check_in_id: uuid.UUID, body: CheckInUpdate, session: DbSession, user: User, tz: TzName
):
    return await checkins.update_check_in(
        session, uuid.UUID(user.profile_id), check_in_id, body, tz
    )
