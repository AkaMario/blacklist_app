import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("BEARER_TOKEN", "test-token")

from src.db.database import db
from src.main import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def auth_headers():
    return {"Authorization": "Bearer test-token"}
