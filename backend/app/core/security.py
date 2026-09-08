"""Password hashing (mock auth mode only) and JWT helpers.

Passwords are NEVER stored raw. Mock auth mode stores a salted PBKDF2-SHA256 hash.
Supabase auth mode delegates all password handling to Supabase Auth.
"""

import base64
import hashlib
import hmac
import secrets
import time
from typing import Any

import jwt

from app.config import settings
from app.core.exceptions import AppError, ErrorCode

PBKDF2_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    salt_b64 = base64.b64encode(salt).decode()
    digest_b64 = base64.b64encode(digest).decode()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_b64}${digest_b64}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_mock_token(token_type: str, subject: str, email: str) -> str:
    if token_type == "access":
        expires_delta = settings.access_token_expire_minutes * 60
    else:
        expires_delta = settings.refresh_token_expire_days * 24 * 3600
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": subject,
        "email": email,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.mock_jwt_secret, algorithm="HS256")


def decode_mock_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.mock_jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise AppError(401, ErrorCode.AUTH_EXPIRED, "The access token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise AppError(401, ErrorCode.AUTH_INVALID, "The access token is invalid.") from exc
    if payload.get("type") != expected_type:
        raise AppError(401, ErrorCode.AUTH_INVALID, "The token type is invalid.")
    return payload
