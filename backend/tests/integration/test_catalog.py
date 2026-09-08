"""Integration tests for the catalog and seed data (Phase 4)."""

from scripts.seed import run_seed
from tests.conftest import auth_headers, signup


async def test_equipment_catalog_seeded(client):
    data = await signup(client)
    resp = await client.get("/api/v1/catalog/equipment", headers=auth_headers(data["access_token"]))
    assert resp.status_code == 200
    slugs = {item["slug"] for item in resp.json()["items"]}
    assert {"bodyweight", "dumbbells", "barbell", "bench", "cable_machine", "treadmill"} <= slugs


async def test_exercises_catalog_seeded_and_filterable(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    resp = await client.get("/api/v1/catalog/exercises", headers=headers)
    assert resp.status_code == 200
    exercises = resp.json()
    assert len(exercises) >= 40

    strength = await client.get(
        "/api/v1/catalog/exercises", params={"workout_type": "strength"}, headers=headers
    )
    assert strength.json()
    assert all(ex["workout_type"] == "strength" for ex in strength.json())

    beginner = await client.get(
        "/api/v1/catalog/exercises", params={"difficulty": "beginner"}, headers=headers
    )
    assert all(ex["difficulty"] == "beginner" for ex in beginner.json())


async def test_exercise_detail_and_404(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    exercises = (await client.get("/api/v1/catalog/exercises", headers=headers)).json()
    exercise_id = exercises[0]["id"]
    resp = await client.get(f"/api/v1/catalog/exercises/{exercise_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == exercise_id

    import uuid

    resp = await client.get(f"/api/v1/catalog/exercises/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "EXERCISE_NOT_FOUND"


async def test_seed_is_idempotent(session):
    from sqlalchemy import func, select

    from app.db.models.catalog import Equipment, Exercise

    first_equipment = await session.scalar(select(func.count()).select_from(Equipment))
    first_exercises = await session.scalar(select(func.count()).select_from(Exercise))
    await run_seed()
    await run_seed()
    second_equipment = await session.scalar(select(func.count()).select_from(Equipment))
    second_exercises = await session.scalar(select(func.count()).select_from(Exercise))
    assert first_equipment == second_equipment
    assert first_exercises == second_exercises
