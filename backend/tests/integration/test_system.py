"""Integration tests for system endpoints (Phase 0)."""


async def test_health(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"]
    assert body["version"]


async def test_version(client):
    resp = await client.get("/api/v1/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["generator_version"] == "rules-v1"


async def test_openapi_docs_available(client):
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"] == "Adaptive Fitness Coach API"


async def test_error_envelope_for_unknown_route(client):
    resp = await client.get("/api/v1/does-not-exist")
    assert resp.status_code == 404
    assert "error" in resp.json()


async def test_request_id_returned(client):
    resp = await client.get("/api/v1/version")
    assert "X-Request-ID" in resp.headers
