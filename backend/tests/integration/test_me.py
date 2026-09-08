"""Integration tests for profile / onboarding endpoints (Phase 3)."""

import uuid

from tests.conftest import (
    auth_headers,
    create_check_in,
    onboarded_user,
    set_accessibility,
    set_equipment,
    set_goals,
    set_profile,
    set_training,
    signup,
)


async def test_patch_profile_persists(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    resp = await client.patch(
        "/api/v1/me",
        json={"name": "Alex", "age": 25, "height_cm": 178, "weight_kg": 80},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Alex"
    assert body["age"] == 25
    assert body["height_cm"] == 178
    assert body["onboarding_completed"] is False


async def test_identity_fields_cannot_be_updated(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    resp = await client.patch("/api/v1/me", json={"email": "hacked@example.com"}, headers=headers)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_goals_upsert_and_get(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    resp = await client.put(
        "/api/v1/me/goals",
        json={"primary_goal": "gain_muscle", "secondary_goal": None, "target_metrics": {}},
        headers=headers,
    )
    assert resp.status_code == 200
    get_resp = await client.get("/api/v1/me/goals", headers=headers)
    assert get_resp.json()["primary_goal"] == "gain_muscle"


async def test_goals_rejects_invalid_primary_goal(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    resp = await client.put(
        "/api/v1/me/goals",
        json={"primary_goal": "become_a_ninja"},
        headers=headers,
    )
    assert resp.status_code == 422


async def test_training_profile_validation(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    resp = await client.put(
        "/api/v1/me/training-profile",
        json={
            "experience_level": "beginner",
            "preferred_days": ["monday", "funday"],
            "session_length_minutes": 45,
        },
        headers=headers,
    )
    assert resp.status_code == 422

    resp = await client.put(
        "/api/v1/me/training-profile",
        json={
            "experience_level": "beginner",
            "preferred_days": ["monday"],
            "session_length_minutes": 20,
        },
        headers=headers,
    )
    assert resp.status_code == 422


async def test_accessibility_persists_immediately(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    await client.put(
        "/api/v1/me/accessibility",
        json={"motion_reduced": True, "voice_enabled": True},
        headers=headers,
    )
    resp = await client.get("/api/v1/me/accessibility", headers=headers)
    body = resp.json()
    assert body["motion_reduced"] is True
    assert body["voice_enabled"] is True
    assert body["haptics_enabled"] is False


async def test_equipment_replacement_is_transactional(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    ids = await set_equipment(client, headers, ["dumbbells", "bench"])
    assert len(ids) == 2

    resp = await client.put(
        "/api/v1/me/equipment", json={"equipment_ids": ids[:1]}, headers=headers
    )
    assert resp.status_code == 200
    get_resp = await client.get("/api/v1/me/equipment", headers=headers)
    assert get_resp.json()["equipment_ids"] == ids[:1]

    bad = await client.put(
        "/api/v1/me/equipment",
        json={"equipment_ids": [str(uuid.uuid4())]},
        headers=headers,
    )
    assert bad.status_code == 404
    get_resp = await client.get("/api/v1/me/equipment", headers=headers)
    assert get_resp.json()["equipment_ids"] == ids[:1]


async def test_notifications_default_and_upsert(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    resp = await client.get("/api/v1/me/notifications", headers=headers)
    assert resp.json()["daily_checkin_reminders"] is True
    await client.put(
        "/api/v1/me/notifications",
        json={
            "daily_checkin_reminders": False,
            "workout_reminders": True,
            "weekly_summary_alerts": False,
        },
        headers=headers,
    )
    resp = await client.get("/api/v1/me/notifications", headers=headers)
    assert resp.json()["daily_checkin_reminders"] is False
    assert resp.json()["weekly_summary_alerts"] is False


async def test_onboarding_complete_rejects_missing_state(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    resp = await client.post("/api/v1/me/onboarding/complete", headers=headers)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "ONBOARDING_INCOMPLETE"
    assert set(resp.json()["error"]["details"]["missing"]) == {
        "profile_basics",
        "goals",
        "training_profile",
        "accessibility",
        "baseline_checkin",
    }


async def test_onboarding_complete_full_flow(client):
    user = await onboarded_user(client, complete_onboarding=False)
    resp = await client.get("/api/v1/me", headers=user["headers"])
    assert resp.json()["onboarding_completed"] is False
    resp = await client.post("/api/v1/me/onboarding/complete", headers=user["headers"])
    assert resp.status_code == 200, resp.text
    resp = await client.get("/api/v1/me", headers=user["headers"])
    assert resp.json()["onboarding_completed"] is True


async def test_onboarding_requires_baseline_checkin(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    await set_profile(client, headers)
    await set_goals(client, headers)
    await set_training(client, headers)
    await set_accessibility(client, headers)
    await set_equipment(client, headers, ["dumbbells"])

    resp = await client.post("/api/v1/me/onboarding/complete", headers=headers)
    assert resp.status_code == 422
    assert resp.json()["error"]["details"]["missing"] == ["baseline_checkin"]

    await create_check_in(client, headers)
    resp = await client.post("/api/v1/me/onboarding/complete", headers=headers)
    assert resp.status_code == 200
