"""Integration tests for check-ins (Phase 5)."""

from tests.conftest import auth_headers, create_check_in, signup


async def test_create_and_get_today(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    check_in = await create_check_in(client, headers)
    resp = await client.get("/api/v1/check-ins/today", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == check_in["id"]
    assert resp.json()["energy_score"] == 7


async def test_duplicate_checkin_same_day_409(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    await create_check_in(client, headers)
    resp = await client.post(
        "/api/v1/check-ins",
        json={
            "energy_score": 5,
            "soreness_map": {},
            "mood_score": 5,
            "sleep_score": 5,
            "stress_score": 5,
            "time_available_minutes": 30,
            "pain_score": None,
        },
        headers=headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CHECKIN_ALREADY_EXISTS"


async def test_update_todays_checkin(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    check_in = await create_check_in(client, headers)
    resp = await client.put(
        f"/api/v1/check-ins/{check_in['id']}",
        json={"energy_score": 4, "time_available_minutes": 30},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["energy_score"] == 4
    assert resp.json()["time_available_minutes"] == 30
    assert resp.json()["sleep_score"] == 7


async def test_update_todays_checkin_can_clear_nullable_fields(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    check_in = await create_check_in(client, headers, {"pain_score": 3})
    resp = await client.put(
        f"/api/v1/check-ins/{check_in['id']}",
        json={"time_available_minutes": None, "pain_score": None},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["time_available_minutes"] is None
    assert resp.json()["pain_score"] is None


async def test_update_rejects_null_soreness_map(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    check_in = await create_check_in(client, headers)
    resp = await client.put(
        f"/api/v1/check-ins/{check_in['id']}",
        json={"soreness_map": None},
        headers=headers,
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "CHECKIN_INVALID"


async def test_scores_validated(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    resp = await client.post(
        "/api/v1/check-ins",
        json={
            "energy_score": 11,
            "soreness_map": {},
            "mood_score": 5,
            "sleep_score": 5,
            "stress_score": 5,
            "time_available_minutes": 30,
            "pain_score": None,
        },
        headers=headers,
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_unknown_region_rejected(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    resp = await client.post(
        "/api/v1/check-ins",
        json={
            "energy_score": 5,
            "soreness_map": {"left_elbow": 3},
            "mood_score": 5,
            "sleep_score": 5,
            "stress_score": 5,
            "time_available_minutes": 30,
            "pain_score": None,
        },
        headers=headers,
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "CHECKIN_INVALID"


async def test_list_checkins_paginated(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    await create_check_in(client, headers)
    resp = await client.get("/api/v1/check-ins", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert len(resp.json()["items"]) == 1


async def test_get_checkin_by_id_and_404(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    check_in = await create_check_in(client, headers)
    resp = await client.get(f"/api/v1/check-ins/{check_in['id']}", headers=headers)
    assert resp.status_code == 200

    import uuid

    resp = await client.get(f"/api/v1/check-ins/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "CHECKIN_NOT_FOUND"


async def test_baseline_checkin_can_omit_time(client):
    data = await signup(client)
    headers = auth_headers(data["access_token"])
    resp = await client.post(
        "/api/v1/check-ins",
        json={
            "energy_score": 6,
            "soreness_map": {},
            "mood_score": 6,
            "sleep_score": 6,
            "stress_score": 6,
            "time_available_minutes": None,
            "pain_score": None,
        },
        headers=headers,
    )
    assert resp.status_code == 201
