"""Centralized application errors and the API error envelope."""

from enum import StrEnum
from typing import Any

from fastapi.responses import JSONResponse


class ErrorCode(StrEnum):
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_INVALID = "AUTH_INVALID"
    AUTH_EXPIRED = "AUTH_EXPIRED"
    AUTH_EMAIL_IN_USE = "AUTH_EMAIL_IN_USE"
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"

    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    ONBOARDING_INCOMPLETE = "ONBOARDING_INCOMPLETE"

    CHECKIN_NOT_FOUND = "CHECKIN_NOT_FOUND"
    CHECKIN_ALREADY_EXISTS = "CHECKIN_ALREADY_EXISTS"
    CHECKIN_INVALID = "CHECKIN_INVALID"

    WORKOUT_NOT_FOUND = "WORKOUT_NOT_FOUND"
    WORKOUT_ALREADY_EXISTS = "WORKOUT_ALREADY_EXISTS"
    WORKOUT_GENERATION_FAILED = "WORKOUT_GENERATION_FAILED"
    WORKOUT_GENERATION_RESTRICTED = "WORKOUT_GENERATION_RESTRICTED"
    WORKOUT_VALIDATION_FAILED = "WORKOUT_VALIDATION_FAILED"

    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_ALREADY_COMPLETED = "SESSION_ALREADY_COMPLETED"
    SESSION_INVALID_STATE = "SESSION_INVALID_STATE"

    EXERCISE_NOT_FOUND = "EXERCISE_NOT_FOUND"
    EQUIPMENT_NOT_FOUND = "EQUIPMENT_NOT_FOUND"

    AI_EXPLANATION_UNAVAILABLE = "AI_EXPLANATION_UNAVAILABLE"
    AI_INSIGHT_UNAVAILABLE = "AI_INSIGHT_UNAVAILABLE"

    WEEKLY_SUMMARY_NOT_FOUND = "WEEKLY_SUMMARY_NOT_FOUND"

    VALIDATION_ERROR = "VALIDATION_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: ErrorCode | str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code if isinstance(code, ErrorCode) else ErrorCode(str(code))
        self.message = message
        self.details = details or {}


def error_response(
    status_code: int, code: str, message: str, details: dict[str, Any]
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


def app_error_response(exc: AppError) -> JSONResponse:
    return error_response(exc.status_code, exc.code.value, exc.message, exc.details)
