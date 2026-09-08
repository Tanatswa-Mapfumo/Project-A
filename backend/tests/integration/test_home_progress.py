"""Integration tests for home and progress (Phase 9)."""

from tests.conftest import auth_headers, onboarded_user, signup


async def test_home_no_data_state(client):
    data = await signup(client)
    resp = await client.get("/api/v1/home", headers=auth_headers(data["access_token"]))
    assert resp.status_code == 200
    body = resp.json()
    assert body["check_in_completed"] is False
    assert body["today_workout"] is None
    assert body["consistency_score"] == 0
    assert body["current_streak"] == 0
    assert body["quick_stats"]["completed_sessions_7d"] == 0


async def test_progress_no_data_state(client):
    data = await signup(client)
    resp = await client.get("/api/v1/progress", headers=auth_headers(data["access_token"]))
    assert resp.status_code == 200
    body = resp.json()
    assert body["consistency_score"] == 0
    assert body["current_streak"] == 0
    assert body["energy_trend"]["direction"] == "insufficient_data"
    assert body["recovery_trend"]["direction"] == "insufficient_data"
    assert body["strength_progression"]["direction"] == "insufficient_data"


async def test_home_after_workout(client):
    user = await onboarded_user(client)
    resp = await client.post(
        "/api/v1/workouts/generate",
        json={"check_in_id": user["check_in_id"]},
        headers=user["headers"],
    )
    workout = resp.json()

    home = (await client.get("/api/v1/home", headers=user["headers"])).json()
    assert home["check_in_completed"] is True
    assert home["today_workout"]["id"] == workout["id"]
    assert home["today_workout"]["type"] == workout["type"]

    session = (
        await client.post(
            "/api/v1/workout-sessions",
            json={"workout_id": workout["id"]},
            headers=user["headers"],
        )
    ).json()
    await client.post(
        f"/api/v1/workout-sessions/{session['id']}/complete",
        json={"rpe": 6},
        headers=user["headers"],
    )

    progress = (await client.get("/api/v1/progress", headers=user["headers"])).json()
    assert progress["completed_sessions_7d"] >= 1
    assert progress["planned_sessions_7d"] >= 1
    assert progress["consistency_score"] > 0
    assert progress["current_streak"] >= 0


async def test_consistency_score_reflects_completion(client):
    user = await onboarded_user(client)
    workout = (
        await client.post(
            "/api/v1/workouts/generate",
            json={"check_in_id": user["check_in_id"]},
            headers=user["headers"],
        )
    ).json()
    session = (
        await client.post(
            "/api/v1/workout-sessions",
            json={"workout_id": workout["id"]},
            headers=user["headers"],
        )
    ).json()
    await client.post(
        f"/api/v1/workout-sessions/{session['id']}/complete",
        json={"rpe": 6},
        headers=user["headers"],
    )
    progress = (await client.get("/api/v1/progress", headers=user["headers"])).json()
    assert progress["consistency_score"] == 100.0
    assert progress["current_streak"] == 1


async def test_history_endpoints(client):
    user = await onboarded_user(client)
    await client.post(
        "/api/v1/workouts/generate",
        json={"check_in_id": user["check_in_id"]},
        headers=user["headers"],
    )
    workouts = (await client.get("/api/v1/progress/workouts", headers=user["headers"])).json()
    assert workouts["total"] == 1
    assert workouts["items"][0]["status"] == "generated"

    checkins = (await client.get("/api/v1/progress/check-ins", headers=user["headers"])).json()
    assert checkins["total"] == 1


async def test_trend_appears_with_data(client):
    user = await onboarded_user(client)
    progress = (await client.get("/api/v1/progress", headers=user["headers"])).json()
    assert progress["energy_trend"]["direction"] == "insufficient_data"
    assert progress["energy_trend"]["change_percent"] is None
