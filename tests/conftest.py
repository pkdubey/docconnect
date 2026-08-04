import django
import os
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docconnect_backend.settings.development')


@pytest.fixture(scope='session')
def django_db_setup():
    pass


@pytest.fixture
def api_client():
    from fastapi.testclient import TestClient
    from fastapi_app.main import app
    return TestClient(app)


@pytest.fixture
def sample_phone():
    return "9876543210"
