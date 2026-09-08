"""HTTP middleware: request IDs and structured access logging."""

import contextvars
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging import get_logger

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

access_logger = get_logger("app.access")


def get_request_id() -> str:
    return request_id_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request_id_var.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        user_id = getattr(request.state, "user_id", "-")
        access_logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%s user_id=%s",
            request_id_var.get(),
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            user_id,
        )
        return response
