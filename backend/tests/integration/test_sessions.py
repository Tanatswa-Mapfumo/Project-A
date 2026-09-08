"""Integration tests for workout sessions (Phase 8)."""

from tests.conftest import onboarded_user


async def generate(client, headers, check_in_id):
    resp = await client.post(
        "/api/v1/workouts/generate", json={"check_in_id": check_in_id}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_start_session_marks_plan_started(client):
    user = await onboarded_user(client)
    workout = await generate(client, user["headers"], user["check_in_id"])

    resp = await client.post(
        "/api/v1/workout-sessions",
        json={"workout_id": workout["id"]},
        headers=user["headers"],
    )
    assert resp.status_code == 201
    session = resp.json()
    assert session["status"] == "in_progress"

    plan = (await client.get(f"/api/v1/workouts/{workout['id']}", headers=user["headers"])).json()
    assert plan["status"] == "started"

    # Idempotent while in progress
    again = await client.post(
        "/api/v1/workout-sessions",
        json={"workout_id": workout["id"]},
        headers=user["headers"],
    )
    assert again.json()["id"] == session["id"]


async def test_complete_session_updates_plan_and_returns_summary(client):
    user = await onboarded_user(client)
    workout = await generate(client, user["headers"], user["check_in_id"])
    session = (
        await client.post(
            "/api/v1/workout-sessions",
            json={"workout_id": workout["id"]},
            headers=user["headers"],
        )
    ).json()

    resp = await client.post(
        f"/api/v1/workout-sessions/{session['id']}/complete",
        json={
            "rpe": 7,
            "modifications": ["reduced_load"],
            "post_soreness_map": {"shoulders": 3},
            "notes": "Last set was difficult.",
        },
        headers=user["headers"],
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["session"]["status"] == "completed"
    assert body["session"]["completed"] is True
    assert body["session"]["rpe"] == 7
    assert body["daily_summary"]["completed_sessions_today"] >= 1

    plan = (await client.get(f"/api/v1/workouts/{workout['id']}", headers=user["headers"])).json()
    assert plan["status"] == "completed"

    # Double complete rejected
    again = await client.post(
        f"/api/v1/workout-sessions/{session['id']}/complete",
        json={"rpe": 8},
        headers=user["headers"],
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "SESSION_ALREADY_COMPLETED"


async def test_invalid_rpe_rejected(client):
    user = await onboarded_user(client)
    workout = await generate(client, user["headers"], user["check_in_id"])
    session = (
        await client.post(
            "/api/v1/workout-sessions",
            json={"workout_id": workout["id"]},
            headers=user["headers"],
        )
    ).json()
    resp = await client.post(
        f"/api/v1/workout-sessions/{session['id']}/complete",
        json={"rpe": 11},
        headers=user["headers"],
    )
    assert resp.status_code == 422


async def test_unknown_post_soreness_region_rejected(client):
    user = await onboarded_user(client)
    workout = await generate(client, user["headers"], user["check_in_id"])
    session = (
        await client.post(
            "/api/v1/workout-sessions",
            json={"workout_id": workout["id"]},
            headers=user["headers"],
        )
    ).json()
    resp = await client.post(
        f"/api/v1/workout-sessions/{session['id']}/complete",
        json={"rpe": 7, "post_soreness_map": {"left_elbow": 4}},
        headers=user["headers"],
    )
    assert resp.status_code == 422


async def test_quit_session_keeps_history(client):
    user = await onboarded_user(client)
    workout = await generate(client, user["headers"], user["check_in_id"])
    session = (
        await client.post(
            "/api/v1/workout-sessions",
            json={"workout_id": workout["id"]},
            headers=user["headers"],
        )
    ).json()
    resp = await client.post(
        f"/api/v1/workout-sessions/{session['id']}/quit",
        json={"notes": "Ran out of time."},
        headers=user["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "quit"
    assert resp.json()["completed"] is False

    get_resp = await client.get(
        f"/api/v1/workout-sessions/{session['id']}", headers=user["headers"]
    )
    assert get_resp.status_code == 200

    plan = (await client.get(f"/api/v1/workouts/{workout['id']}", headers=user["headers"])).json()
    assert plan["status"] == "generated"


async def test_session_ownership(client):
    user_a = await onboarded_user(client)
    user_b = await onboarded_user(client)
    workout = await generate(client, user_a["headers"], user_a["check_in_id"])
    session = (
        await client.post(
            "/api/v1/workout-sessions",
            json={"workout_id": workout["id"]},
            headers=user_a["headers"],
        )
    ).json()

    resp = await client.get(f"/api/v1/workout-sessions/{session['id']}", headers=user_b["headers"])
    assert resp.status_code == 404

    resp = await client.post(
        f"/api/v1/workout-sessions/{session['id']}/complete",
        json={"rpe": 5},
        headers=user_b["headers"],
    )
    assert resp.status_code == 404


async def test_cannot_start_other_users_workout(client):
    user_a = await onboarded_user(client)
    user_b = await onboarded_user(client)
    workout = await generate(client, user_a["headers"], user_a["check_in_id"])
    resp = await client.post(
        "/api/v1/workout-sessions",
        json={"workout_id": workout["id"]},
        headers=user_b["headers"],
    )
    assert resp.status_code == 404
