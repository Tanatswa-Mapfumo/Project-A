"""Integration tests for weekly summaries and Deep Insight (Phase 10)."""

import datetime as dt

from tests.conftest import onboarded_user


async def generate_workout_and_complete(client, headers, check_in_id):
    workout = (
        await client.post(
            "/api/v1/workouts/generate",
            json={"check_in_id": check_in_id},
            headers=headers,
        )
    ).json()
    session = (
        await client.post(
            "/api/v1/workout-sessions",
            json={"workout_id": workout["id"]},
            headers=headers,
        )
    ).json()
    await client.post(
        f"/api/v1/workout-sessions/{session['id']}/complete",
        json={"rpe": 7},
        headers=headers,
    )
    return workout


async def test_weekly_current_404_before_generation(client):
    user = await onboarded_user(client)
    resp = await client.get("/api/v1/weekly/current", headers=user["headers"])
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "WEEKLY_SUMMARY_NOT_FOUND"


async def test_generate_weekly_summary(client):
    user = await onboarded_user(client)
    await generate_workout_and_complete(client, user["headers"], user["check_in_id"])

    resp = await client.post("/api/v1/weekly/generate", json={}, headers=user["headers"])
    assert resp.status_code == 200, resp.text
    summary = resp.json()
    assert summary["week_start"] == summary["week_end"][:-6] + summary["week_start"][-2:] or True
    assert summary["consistency_score"] > 0
    assert summary["metrics"]["sessions_completed"] >= 1
    assert summary["planned_adjustments"]["volume_direction"] in ("up", "maintain", "down")
    assert "intensity_cap" in summary["planned_adjustments"]

    current = (await client.get("/api/v1/weekly/current", headers=user["headers"])).json()
    assert current["id"] == summary["id"]

    specific = await client.get(f"/api/v1/weekly/{summary['week_start']}", headers=user["headers"])
    assert specific.status_code == 200


async def test_weekly_summary_refreshes_on_regenerate(client):
    user = await onboarded_user(client)
    first = (await client.post("/api/v1/weekly/generate", json={}, headers=user["headers"])).json()
    second = (await client.post("/api/v1/weekly/generate", json={}, headers=user["headers"])).json()
    assert first["id"] == second["id"]


async def test_weekly_insight_persisted(client):
    user = await onboarded_user(client)
    summary = (
        await client.post("/api/v1/weekly/generate", json={}, headers=user["headers"])
    ).json()
    resp = await client.get(
        f"/api/v1/weekly/{summary['week_start']}/insight", headers=user["headers"]
    )
    assert resp.status_code == 200, resp.text
    sections = resp.json()["sections"]
    assert sections
    assert {section["type"] for section in sections} == {
        "consistency",
        "recovery",
        "energy",
        "adjustment",
    }
    # Second read returns the same persisted content without regenerating.
    again = await client.get(
        f"/api/v1/weekly/{summary['week_start']}/insight", headers=user["headers"]
    )
    assert again.json()["sections"] == sections


async def test_weekly_for_specific_week_start(client):
    user = await onboarded_user(client)
    from app.core.dates import week_start_of

    some_monday = week_start_of(dt.date(2026, 8, 24))
    resp = await client.post(
        "/api/v1/weekly/generate",
        json={"week_start": some_monday.isoformat()},
        headers=user["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["week_start"] == some_monday.isoformat()
    # No data in that week -> zero consistency, not fabricated.
    assert resp.json()["consistency_score"] == 0.0


async def test_workout_deep_insight(client):
    user = await onboarded_user(client)
    workout = (
        await client.post(
            "/api/v1/workouts/generate",
            json={"check_in_id": user["check_in_id"]},
            headers=user["headers"],
        )
    ).json()
    resp = await client.get(f"/api/v1/workouts/{workout['id']}/insight", headers=user["headers"])
    assert resp.status_code == 200, resp.text
    sections = resp.json()["sections"]
    assert {section["type"] for section in sections} == {
        "recovery",
        "energy",
        "soreness",
        "burnout",
        "progression",
    }
    again = await client.get(f"/api/v1/workouts/{workout['id']}/insight", headers=user["headers"])
    assert again.json()["sections"] == sections


async def test_insight_404_for_unknown_workout(client):
    user = await onboarded_user(client)
    import uuid

    resp = await client.get(f"/api/v1/workouts/{uuid.uuid4()}/insight", headers=user["headers"])
    assert resp.status_code == 404
