import uuid


VALID_DATA = {
    "email": "cliente@example.com",
    "app_uuid": "123e4567-e89b-12d3-a456-426614174000",
    "blocked_reason": "Spam activity",
}


def test_ping_is_public(client):
    response = client.get("/blacklists/ping")

    assert response.status_code == 200
    assert response.get_json() == {"message": "pong"}


def test_create_requires_authorization(client):
    response = client.post("/blacklists", json=VALID_DATA)

    assert response.status_code == 401
    assert response.get_json()["error"] == "Unauthorized"


def test_create_rejects_invalid_authorization(client):
    response = client.post(
        "/blacklists",
        json=VALID_DATA,
        headers={"Authorization": "Basic test-token"},
    )

    assert response.status_code == 401


def test_create_rejects_missing_token_value(client):
    response = client.post(
        "/blacklists",
        json=VALID_DATA,
        headers={"Authorization": "Bearer"},
    )

    assert response.status_code == 401


def test_create_rejects_wrong_token(client):
    response = client.post(
        "/blacklists",
        json=VALID_DATA,
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 401


def test_create_reports_missing_token_configuration(client, auth_headers, monkeypatch):
    monkeypatch.delenv("BEARER_TOKEN")

    response = client.post("/blacklists", json=VALID_DATA, headers=auth_headers)

    assert response.status_code == 500
    assert "not configured" in response.get_json()["message"]


def test_create_blacklist_entry(client, auth_headers):
    response = client.post("/blacklists", json=VALID_DATA, headers=auth_headers)

    body = response.get_json()
    assert response.status_code == 201
    assert body["email"] == VALID_DATA["email"]
    assert body["message"].startswith("Email cliente@example.com")
    assert uuid.UUID(body["id"])
    assert body["created_at"]


def test_create_rejects_empty_body(client, auth_headers):
    response = client.post("/blacklists", json={}, headers=auth_headers)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Request body is required"


def test_create_rejects_invalid_fields(client, auth_headers):
    invalid_data = {
        "email": "not-an-email",
        "app_uuid": "not-a-uuid",
        "blocked_reason": "x" * 256,
    }

    response = client.post("/blacklists", json=invalid_data, headers=auth_headers)

    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad Request"
    assert set(response.get_json()["details"]) == {
        "email",
        "app_uuid",
        "blocked_reason",
    }


def test_create_rejects_missing_required_fields(client, auth_headers):
    response = client.post(
        "/blacklists",
        json={"blocked_reason": "Missing fields"},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert set(response.get_json()["details"]) == {"email", "app_uuid"}


def test_duplicate_email_returns_conflict(client, auth_headers):
    client.post("/blacklists", json=VALID_DATA, headers=auth_headers)

    response = client.post("/blacklists", json=VALID_DATA, headers=auth_headers)

    assert response.status_code == 409
    assert response.get_json()["error"] == "Conflict"


def test_check_existing_blacklist_entry(client, auth_headers):
    client.post("/blacklists", json=VALID_DATA, headers=auth_headers)

    response = client.get(
        f"/blacklists/{VALID_DATA['email']}", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "is_blacklisted": True,
        "email": VALID_DATA["email"],
        "blocked_reason": VALID_DATA["blocked_reason"],
    }


def test_check_unknown_email(client, auth_headers):
    response = client.get(
        "/blacklists/unknown@example.com", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "is_blacklisted": False,
        "email": "unknown@example.com",
        "blocked_reason": None,
    }


def test_check_requires_authorization(client):
    response = client.get("/blacklists/unknown@example.com")

    assert response.status_code == 401
