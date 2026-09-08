"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    catalog,
    checkins,
    home,
    me,
    progress,
    sessions,
    system,
    weekly,
    workouts,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(catalog.router)
api_router.include_router(checkins.router)
api_router.include_router(workouts.router)
api_router.include_router(sessions.router)
api_router.include_router(home.router)
api_router.include_router(progress.router)
api_router.include_router(weekly.router)
api_router.include_router(system.router)
