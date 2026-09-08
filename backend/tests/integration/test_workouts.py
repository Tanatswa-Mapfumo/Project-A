"""Integration tests for workout generation (Phase 6-7, critical scenarios A-G)."""

from app.rules.duration import estimate_exercise_seconds
from tests.conftest import auth_headers, create_check_in, onboarded_user, signup


async def generate(client, headers, check_in_id):
    resp = await client.post(
        "/api/v1/workouts/generate", json={"check_in_id": check_in_id}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def estimated_seconds(workout: dict) -> int:
    total = 0
    for ex in workout["exercises"]:
        total += estimate_exercise_seconds(ex["sets"], ex["rest_seconds"], ex["duration_seconds"])
    return total


async def test_scenario_a_normal_workout(client):
    user = await onboarded_user(client, goal="gain_muscle")
    workout = await generate(client, user["headers"], user["check_in_id"])
    assert workout["intensity"] in ("moderate", "high")
    assert workout["duration_minutes"] == 45
    assert workout["short_explanation"]
    for ex in workout["exercises"]:
        assert ex["name"]
        assert ex["reps_min"] and ex["reps_max"] or ex["duration_seconds"]
    assert estimated_seconds(workout) <= 45 * 60
    assert workout["generator_version"] == "rules-v1"


async def test_scenario_b_sore_quads_excluded(client):
    user = await onboarded_user(client, checkin={"soreness_map": {"quads": 9}})
    workout = await generate(client, user["headers"], user["check_in_id"])
    catalog = (await client.get("/api/v1/catalog/exercises", headers=user["headers"])).json()
    by_id = {ex["id"]: ex for ex in catalog}
    for row in workout["exercises"]:
        primary = by_id[row["exercise_id"]]["primary_muscle_groups"]
        assert "quadriceps" not in primary


async def test_scenario_c_low_recovery_forces_low_intensity(client):
    user = await onboarded_user(
        client,
        checkin={"energy_score": 3, "sleep_score": 2, "stress_score": 9},
    )
    workout = await generate(client, user["headers"], user["check_in_id"])
    assert workout["intensity"] == "low"


async def test_scenario_d_no_equipment_bodyweight_only(client):
    user = await onboarded_user(client, equipment=[])
    workout = await generate(client, user["headers"], user["check_in_id"])
    catalog = (await client.get("/api/v1/catalog/exercises", headers=user["headers"])).json()
    by_id = {ex["id"]: ex for ex in catalog}
    for row in workout["exercises"]:
        equipment = by_id[row["exercise_id"]]["equipment"]
        assert set(equipment) <= {"bodyweight", "yoga_mat"}, equipment


async def test_scenario_e_short_session(client):
    user = await onboarded_user(client, length=15, checkin={"time_available_minutes": 15})
    workout = await generate(client, user["headers"], user["check_in_id"])
    assert workout["duration_minutes"] == 15
    assert estimated_seconds(workout) <= 15 * 60
    assert workout["exercises"]


async def test_scenario_f_ai_offline_falls_back(client, monkeypatch):
    import app.ai.base as ai_base

    monkeypatch.setattr(ai_base.settings, "ai_provider", "gemini")
    monkeypatch.setattr(ai_base.settings, "gemini_api_key", "")
    try:
        user = await onboarded_user(client)
        workout = await generate(client, user["headers"], user["check_in_id"])
        assert workout["short_explanation"]
        assert "intensity" in workout["short_explanation"].lower()
    finally:
        monkeypatch.setattr(ai_base.settings, "ai_provider", "mock")


async def test_generate_is_idempotent(client):
    user = await onboarded_user(client)
    first = await generate(client, user["headers"], user["check_in_id"])
    second = await generate(client, user["headers"], user["check_in_id"])
    assert first["id"] == second["id"]


async def test_generate_requires_checkin(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    import uuid

    resp = await client.post(
        "/api/v1/workouts/generate",
        json={"check_in_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "CHECKIN_NOT_FOUND"


async def test_generate_requires_onboarding(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    check_in = await create_check_in(client, headers)
    resp = await client.post(
        "/api/v1/workouts/generate",
        json={"check_in_id": check_in["id"]},
        headers=headers,
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "ONBOARDING_INCOMPLETE"


async def test_generation_restricted_on_high_pain(client):
    user = await onboarded_user(client, checkin={"pain_score": 9})
    resp = await client.post(
        "/api/v1/workouts/generate",
        json={"check_in_id": user["check_in_id"]},
        headers=user["headers"],
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "WORKOUT_GENERATION_RESTRICTED"


async def test_today_and_list_endpoints(client):
    user = await onboarded_user(client)
    workout = await generate(client, user["headers"], user["check_in_id"])

    resp = await client.get("/api/v1/workouts/today", headers=user["headers"])
    assert resp.status_code == 200
    assert resp.json()["workout"]["id"] == workout["id"]

    resp = await client.get("/api/v1/workouts", headers=user["headers"])
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    resp = await client.get(f"/api/v1/workouts/{workout['id']}", headers=user["headers"])
    assert resp.status_code == 200
    assert len(resp.json()["exercises"]) == len(workout["exercises"])


async def test_explanation_endpoint(client):
    user = await onboarded_user(client)
    workout = await generate(client, user["headers"], user["check_in_id"])
    resp = await client.get(
        f"/api/v1/workouts/{workout['id']}/explanation", headers=user["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["short_explanation"] == workout["short_explanation"]


async def test_deterministic_across_users(client):
    user_a = await onboarded_user(client)
    user_b = await onboarded_user(client)
    workout_a = await generate(client, user_a["headers"], user_a["check_in_id"])
    workout_b = await generate(client, user_b["headers"], user_b["check_in_id"])
    assert [ex["slug"] for ex in workout_a["exercises"]] == [
        ex["slug"] for ex in workout_b["exercises"]
    ]
