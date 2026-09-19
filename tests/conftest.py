import os
import django
import pytest

# Use test settings so tests run against docconnect_test DB, not the real DB.
# test.py inherits base.py and overrides DATABASE NAME + disables SMS/cache.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docconnect_backend.settings.test')
django.setup()


@pytest.fixture(scope='session')
def django_db_setup():
    """Let pytest-django manage the test database lifecycle."""
    pass


@pytest.fixture
def api_client():
    """FastAPI TestClient — shares the same Django ORM/DB as the test."""
    from fastapi.testclient import TestClient
    from fastapi_app.main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_phone():
    return "9876543210"
