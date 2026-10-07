def test_health_endpoint(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_update_list_and_delete_target(client):
    payload = {
        "name": "Documentation website",
        "kind": "http",
        "url": "https://example.com",
        "interval_seconds": 60,
        "timeout_seconds": 5,
    }

    unauthorized = client.post("/api/targets", json=payload)
    assert unauthorized.status_code == 401

    created = client.post(
        "/api/targets",
        json=payload,
        headers={"X-API-Key": "test-key"},
    )
    assert created.status_code == 201
    target = created.json()
    assert target["name"] == "Documentation website"
    assert target["kind"] == "http"
    assert target["enabled"] is True

    listed = client.get("/api/targets")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch(
        f"/api/targets/{target['id']}",
        json={"name": "Updated website", "enabled": False},
        headers={"X-API-Key": "test-key"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated website"
    assert updated.json()["enabled"] is False

    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["total"] == 1
    assert dashboard.json()["enabled"] == 0

    deleted = client.delete(
        f"/api/targets/{target['id']}",
        headers={"X-API-Key": "test-key"},
    )
    assert deleted.status_code == 204
    assert client.get("/api/targets").json() == []


def test_target_validation_returns_clear_error(client):
    response = client.post(
        "/api/targets",
        json={
            "name": "Broken target",
            "kind": "tcp",
            "url": "not-a-url",
        },
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 422
