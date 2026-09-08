"""Workout session endpoints (section 18)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TzName
from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.session import (
    SessionCompleteOut,
    SessionCompleteRequest,
    SessionOut,
    SessionQuitRequest,
    SessionStartRequest,
)
from app.services import sessions

router = APIRouter(prefix="/workout-sessions", tags=["Sessions"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
User = Annotated[CurrentUser, Depends(get_current_user)]


@router.post(
    "",
    response_model=SessionOut,
    status_code=201,
    summary="Start a workout session",
    description="Starts a session for the given workout plan and marks the plan as "
    "started. Idempotent while a session is in progress.",
    responses={404: {"description": "Workout not found."}, 409: {"description": "Invalid state."}},
)
async def start_session(body: SessionStartRequest, session: DbSession, user: User):
    return await sessions.start_session(session, uuid.UUID(user.profile_id), body.workout_id)


@router.get(
    "/{session_id}",
    response_model=SessionOut,
    summary="Get a session",
    description="Returns one workout session owned by the authenticated user.",
    responses={404: {"description": "Session not found."}},
)
async def get_session(session_id: uuid.UUID, session: DbSession, user: User):
    return await sessions.get_session(session, uuid.UUID(user.profile_id), session_id)


@router.post(
    "/{session_id}/complete",
    response_model=SessionCompleteOut,
    summary="Complete a workout session",
    description="Records RPE, modifications, post-workout soreness, and notes. Updates "
    "both session and plan status to completed and returns a daily summary.",
    responses={404: {"description": "Session not found."}, 409: {"description": "Invalid state."}},
)
async def complete_session(
    session_id: uuid.UUID, body: SessionCompleteRequest, session: DbSession, user: User, tz: TzName
):
    return await sessions.complete_session(
        session, uuid.UUID(user.profile_id), session_id, body, tz
    )


@router.post(
    "/{session_id}/quit",
    response_model=SessionOut,
    summary="Quit a workout session",
    description="Marks the session as quit without deleting it. The plan becomes "
    "available to start again.",
    responses={404: {"description": "Session not found."}, 409: {"description": "Invalid state."}},
)
async def quit_session(
    session_id: uuid.UUID, body: SessionQuitRequest, session: DbSession, user: User
):
    return await sessions.quit_session(session, uuid.UUID(user.profile_id), session_id, body)
