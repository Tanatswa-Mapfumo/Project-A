"""Test configuration.

Tests run against an isolated SQLite database (aiosqlite) so they need no
external services. Production and staging use PostgreSQL (asyncpg); see
DECISIONS.md. A template database is built once per session (schema + seed),
then copied per test for full isolation.
"""

import os
import uuid
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
TMP_DIR = TEST_DIR / ".tmp"
TEMPLATE_DB = TMP_DIR / "template.db"

os.environ.setdefault("AUTH_MODE", "mock")
os.environ.setdefault("AI_PROVIDER", "mock")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("MOCK_JWT_SECRET", "test-secret-not-for-production-0123456789")
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{TEMPLATE_DB}")
os.environ.setdefault("FRONTEND_ORIGINS", "http://localhost:3000")
os.environ.setdefault("ENABLE_DOCS", "true")

import asyncio  # noqa: E402
import datetime as dt  # noqa: E402
import shutil  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

import app.db.models  # noqa: E402, F401
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def build_template_db():
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    if TEMPLATE_DB.exists():
        TEMPLATE_DB.unlink()

    async def _build():
        engine = create_async_engine(f"sqlite+aiosqlite:///{TEMPLATE_DB}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
        from scripts.seed import run_seed

        await run_seed()

    asyncio.run(_build())
    yield


@pytest.fixture
async def db_engine(tmp_path):
    db_path = tmp_path / "test.db"
    shutil.copy(TEMPLATE_DB, db_path)
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as s:
        yield s


@pytest.fixture
async def client(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def auth_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


async def signup(client: AsyncClient, email: str | None = None) -> dict:
    email = email or f"user-{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "strong-password-1"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return {"email": email, "access_token": data["access_token"], "user_id": data["user"]["id"]}


async def set_profile(client: AsyncClient, headers: dict) -> None:
    resp = await client.patch(
        "/api/v1/me",
        json={
            "name": "Test User",
            "age": 30,
            "height_cm": 178,
            "weight_kg": 80,
            "gender": "non_binary",
            "country": "United Kingdom",
            "timezone": "UTC",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text


async def set_goals(client: AsyncClient, headers: dict, primary_goal: str = "gain_muscle") -> None:
    resp = await client.put(
        "/api/v1/me/goals",
        json={"primary_goal": primary_goal, "secondary_goal": None, "target_metrics": {}},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text


WEEKDAYS = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}


def today_weekday_name() -> str:
    return WEEKDAYS[dt.datetime.now(dt.UTC).date().weekday()]


async def set_training(
    client: AsyncClient,
    headers: dict,
    experience: str = "beginner",
    length: int = 45,
    days: list[str] | None = None,
) -> None:
    days = days or [today_weekday_name()]
    resp = await client.put(
        "/api/v1/me/training-profile",
        json={
            "experience_level": experience,
            "preferred_days": days,
            "session_length_minutes": length,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text


async def set_accessibility(client: AsyncClient, headers: dict) -> None:
    resp = await client.put(
        "/api/v1/me/accessibility",
        json={
            "screen_reader_enabled": False,
            "high_contrast": False,
            "simple_mode": False,
            "motion_reduced": True,
            "voice_enabled": True,
            "haptics_enabled": True,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text


async def get_equipment_id(client: AsyncClient, headers: dict, slug: str) -> str:
    resp = await client.get("/api/v1/catalog/equipment", headers=headers)
    assert resp.status_code == 200, resp.text
    for item in resp.json()["items"]:
        if item["slug"] == slug:
            return item["id"]
    raise AssertionError(f"Equipment slug not found: {slug}")


async def set_equipment(client: AsyncClient, headers: dict, slugs: list[str]) -> list[str]:
    ids = [await get_equipment_id(client, headers, slug) for slug in slugs]
    resp = await client.put("/api/v1/me/equipment", json={"equipment_ids": ids}, headers=headers)
    assert resp.status_code == 200, resp.text
    return ids


DEFAULT_CHECKIN = {
    "energy_score": 7,
    "soreness_map": {},
    "mood_score": 7,
    "sleep_score": 7,
    "stress_score": 4,
    "time_available_minutes": 45,
    "pain_score": None,
}


async def create_check_in(
    client: AsyncClient, headers: dict, overrides: dict | None = None
) -> dict:
    payload = {**DEFAULT_CHECKIN, **(overrides or {})}
    resp = await client.post("/api/v1/check-ins", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def onboarded_user(
    client: AsyncClient,
    *,
    goal: str = "gain_muscle",
    experience: str = "beginner",
    length: int = 45,
    equipment: list[str] | None = None,
    checkin: dict | None = None,
    complete_onboarding: bool = True,
) -> dict:
    user = await signup(client)
    headers = auth_headers(user["access_token"])
    await set_profile(client, headers)
    await set_goals(client, headers, goal)
    await set_training(client, headers, experience, length)
    await set_accessibility(client, headers)
    equipment_ids = await set_equipment(
        client, headers, equipment if equipment is not None else ["dumbbells", "bench"]
    )
    check_in = await create_check_in(client, headers, checkin or {})
    if complete_onboarding:
        resp = await client.post("/api/v1/me/onboarding/complete", headers=headers)
        assert resp.status_code == 200, resp.text
    return {
        **user,
        "headers": headers,
        "check_in_id": check_in["id"],
        "equipment_ids": equipment_ids,
    }
