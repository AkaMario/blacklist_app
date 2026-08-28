import pytest
from marshmallow import ValidationError

from src.models.blacklist import (
    BlacklistCheckResponseSchema,
    BlacklistCreateSchema,
)


VALID_DATA = {
    "email": "user@example.com",
    "app_uuid": "123e4567-e89b-12d3-a456-426614174000",
}


def test_create_schema_accepts_optional_reason():
    result = BlacklistCreateSchema().load(VALID_DATA)

    assert result["email"] == "user@example.com"
    assert result.get("blocked_reason") is None


def test_create_schema_rejects_unknown_fields():
    with pytest.raises(ValidationError) as error:
        BlacklistCreateSchema().load({**VALID_DATA, "extra": "value"})

    assert "Unknown field" in str(error.value)


def test_check_response_schema_serializes_result():
    result = BlacklistCheckResponseSchema().dump(
        {
            "is_blacklisted": True,
            "email": "user@example.com",
            "blocked_reason": "Fraud",
        }
    )

    assert result["is_blacklisted"] is True
    assert result["blocked_reason"] == "Fraud"
