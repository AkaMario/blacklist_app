from types import SimpleNamespace

import pytest

from src.models.errors import ConflictError
from src.services.blacklist_service import BlacklistService


class FakeRepository:
    def __init__(self, blacklist=None):
        self.blacklist = blacklist
        self.created_data = None

    def create(self, data):
        self.created_data = data
        return SimpleNamespace(
            id=data["id"],
            email=data["email"],
            created_at=SimpleNamespace(isoformat=lambda: "2026-08-28T12:00:00"),
        )

    def get_by_email(self, email):
        return self.blacklist


def test_add_to_blacklist_builds_entry():
    service = BlacklistService()
    repository = FakeRepository()
    service.repository = repository

    result = service.add_to_blacklist(
        email="user@example.com",
        app_uuid="123e4567-e89b-12d3-a456-426614174000",
        blocked_reason="Abuse",
        ip_address="127.0.0.1",
    )

    assert result["email"] == "user@example.com"
    assert result["created_at"] == "2026-08-28T12:00:00"
    assert repository.created_data["ip_address"] == "127.0.0.1"
    assert repository.created_data["blocked_reason"] == "Abuse"


def test_check_blacklist_when_entry_exists():
    service = BlacklistService()
    service.repository = FakeRepository(
        SimpleNamespace(blocked_reason="Fraud")
    )

    assert service.check_blacklist("user@example.com") == {
        "is_blacklisted": True,
        "email": "user@example.com",
        "blocked_reason": "Fraud",
    }


def test_check_blacklist_when_entry_does_not_exist():
    service = BlacklistService()
    service.repository = FakeRepository()

    assert service.check_blacklist("user@example.com") == {
        "is_blacklisted": False,
        "email": "user@example.com",
        "blocked_reason": None,
    }


def test_repository_raises_conflict_error_for_duplicate(client, auth_headers):
    response = client.post(
        "/blacklists",
        json={
            "email": "duplicate@example.com",
            "app_uuid": "123e4567-e89b-12d3-a456-426614174000",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201

    response = client.post(
        "/blacklists",
        json={
            "email": "duplicate@example.com",
            "app_uuid": "123e4567-e89b-12d3-a456-426614174000",
        },
        headers=auth_headers,
    )
    assert response.status_code == 409
