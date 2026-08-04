"""
Doctor profile endpoint tests — README section 11
"""
import hashlib
import pytest
from datetime import timedelta


def _get_token(api_client, phone="9811111111"):
    from django.utils import timezone
    from apps.accounts.models import OTPChallenge
    otp = "654321"
    OTPChallenge.objects.create(
        phone=phone, purpose="LOGIN",
        otp_hash=hashlib.sha256(otp.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    resp = api_client.post("/api/v1/auth/verify-otp/", json={"phone": phone, "otp": otp, "purpose": "LOGIN"})
    return resp.json()["access_token"]


@pytest.mark.django_db
def test_create_doctor_profile(api_client):
    token = _get_token(api_client)
    response = api_client.post(
        "/api/v1/doctors/profile/",
        json={
            "first_name": "Rahul",
            "last_name": "Sharma",
            "headline": "Cardiologist",
            "experience_years": 5,
            "professional_location": {"city": "Mumbai", "state": "Maharashtra"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Rahul"
    assert data["full_name"] == "Rahul Sharma"


@pytest.mark.django_db
def test_get_my_profile(api_client):
    token = _get_token(api_client, "9822222222")
    api_client.post(
        "/api/v1/doctors/profile/",
        json={"first_name": "Priya", "last_name": "Patel", "experience_years": 3,
              "professional_location": {"city": "Delhi", "state": "Delhi"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = api_client.get(
        "/api/v1/doctors/profile/me/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "Priya"


@pytest.mark.django_db
def test_create_profile_duplicate(api_client):
    token = _get_token(api_client, "9833333333")
    payload = {"first_name": "Test", "last_name": "Doc", "experience_years": 1,
               "professional_location": {"city": "Pune", "state": "Maharashtra"}}
    api_client.post("/api/v1/doctors/profile/", json=payload, headers={"Authorization": f"Bearer {token}"})
    response = api_client.post("/api/v1/doctors/profile/", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 409


@pytest.mark.django_db
def test_search_doctors_unauthenticated(api_client):
    response = api_client.get("/api/v1/doctors/search/")
    assert response.status_code == 403
