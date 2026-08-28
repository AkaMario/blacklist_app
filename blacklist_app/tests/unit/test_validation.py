import pytest

from src.models.errors import BadRequestError
from src.utils.validation import get_client_ip, validate_uuid


def test_validate_uuid_accepts_valid_value():
    assert validate_uuid("123e4567-e89b-12d3-a456-426614174000") is True


def test_validate_uuid_rejects_invalid_value():
    with pytest.raises(BadRequestError, match="Invalid UUID format"):
        validate_uuid("invalid-uuid")


def test_get_client_ip_uses_forwarded_header(app_request):
    assert get_client_ip(app_request) == "203.0.113.10"


def test_get_client_ip_uses_remote_address(app_request_without_forwarded):
    assert get_client_ip(app_request_without_forwarded) == "127.0.0.1"


@pytest.fixture()
def app_request():
    from flask import Flask

    app = Flask(__name__)
    with app.test_request_context(
        "/", headers={"X-Forwarded-For": "203.0.113.10, 10.0.0.1"}
    ):
        yield __import__("flask").request


@pytest.fixture()
def app_request_without_forwarded():
    from flask import Flask

    app = Flask(__name__)
    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "127.0.0.1"}):
        yield __import__("flask").request
