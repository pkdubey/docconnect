"""
Availability endpoint tests — README section 11
"""
import pytest


@pytest.mark.django_db
def test_list_availability_unauthenticated(api_client):
    response = api_client.get("/api/v1/availability/me/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_list_shift_requirements_unauthenticated(api_client):
    response = api_client.get("/api/v1/shifts/requirements/")
    assert response.status_code == 403
