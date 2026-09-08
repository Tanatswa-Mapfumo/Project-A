"""FastAPI application entrypoint."""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_router
from app.config import settings
from app.core.exceptions import AppError, app_error_response, error_response
from app.core.logging import get_logger, setup_logging
from app.core.middleware import AccessLogMiddleware, RequestIDMiddleware

setup_logging()
logger = get_logger("app.main")

TAGS_METADATA = [
    {"name": "Auth", "description": "Signup, login, and token management."},
    {"name": "Profile", "description": "Profile and onboarding configuration."},
    {"name": "Catalog", "description": "Equipment and exercise catalogs."},
    {"name": "Check-Ins", "description": "Daily recovery check-ins."},
    {"name": "Workouts", "description": "Adaptive workout generation and retrieval."},
    {"name": "Sessions", "description": "Workout session lifecycle."},
    {"name": "Progress", "description": "Home dashboard and progress analytics."},
    {"name": "Weekly", "description": "Weekly summaries and macro-adjustments."},
    {"name": "System", "description": "Health and version."},
]


def create_app() -> FastAPI:
    docs_kwargs = (
        {"docs_url": "/docs", "redoc_url": "/redoc", "openapi_url": "/openapi.json"}
        if settings.enable_docs
        else {"docs_url": None, "redoc_url": None, "openapi_url": None}
    )
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Backend API for the Adaptive Fitness Coach: deterministic adaptive workout "
            "generation with AI-generated explanations."
        ),
        openapi_tags=TAGS_METADATA,
        **docs_kwargs,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(RequestIDMiddleware)

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return app_error_response(exc)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = {
            "errors": jsonable_encoder(
                exc.errors(), custom_encoder={Exception: lambda error: str(error)}
            )
        }
        return error_response(422, "VALIDATION_ERROR", "The request body is invalid.", details)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "VALIDATION_ERROR" if exc.status_code in (400, 422) else "INTERNAL_ERROR"
        return error_response(exc.status_code, code, str(exc.detail), {})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error path=%s", request.url.path)
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred.", {})

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
