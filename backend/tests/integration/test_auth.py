"""Integration tests for auth (Phase 2)."""

import uuid

from tests.conftest import auth_headers, onboarded_user, signup


async def test_signup_returns_tokens(client):
    data = await signup(client)
    assert data["access_token"]
    assert uuid.UUID(data["user_id"])


async def test_signup_duplicate_email_409(client):
    await signup(client, "same@example.com")
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "same@example.com", "password": "strong-password-1"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "AUTH_EMAIL_IN_USE"


async def test_login_and_refresh(client):
    email = "login@example.com"
    await signup(client, email)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strong-password-1"},
    )
    assert resp.status_code == 200, resp.text
    tokens = resp.json()
    refresh_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_resp.status_code == 200
    assert refresh_resp.json()["access_token"]


async def test_login_wrong_password_401(client):
    await signup(client, "wrongpass@example.com")
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "not-the-password"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"


async def test_protected_endpoint_requires_token(client):
    resp = await client.get("/api/v1/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_invalid_token_rejected(client):
    resp = await client.get("/api/v1/me", headers=auth_headers("not-a-real-token"))
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "AUTH_INVALID"


async def test_forgot_password_returns_200(client):
    await signup(client, "forgot@example.com")
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": "forgot@example.com"})
    assert resp.status_code == 200


async def test_logout_returns_204(client):
    data = await signup(client)
    resp = await client.post("/api/v1/auth/logout", headers=auth_headers(data["access_token"]))
    assert resp.status_code == 204


async def test_user_cannot_access_other_users_resources(client):
    user_a = await onboarded_user(client)
    user_b = await onboarded_user(client)

    checkin_a = await client.get("/api/v1/check-ins/today", headers=user_a["headers"])
    checkin_id = checkin_a.json()["id"]

    resp = await client.get(f"/api/v1/check-ins/{checkin_id}", headers=user_b["headers"])
    assert resp.status_code == 404

    workout = await client.post(
        "/api/v1/workouts/generate",
        json={"check_in_id": user_a["check_in_id"]},
        headers=user_a["headers"],
    )
    assert workout.status_code == 200
    workout_id = workout.json()["id"]

    resp = await client.get(f"/api/v1/workouts/{workout_id}", headers=user_b["headers"])
    assert resp.status_code == 404
