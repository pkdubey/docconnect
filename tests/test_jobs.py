"""
Jobs endpoint tests — README section 11
"""
import pytest


@pytest.mark.django_db
def test_list_jobs_unauthenticated(api_client):
    response = api_client.get("/api/v1/jobs/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_get_nonexistent_job(api_client):
    import hashlib
    from datetime import timedelta
    from django.utils import timezone
    from apps.accounts.models import OTPChallenge

    phone = "9844444444"
    otp = "111222"
    OTPChallenge.objects.create(
        phone=phone, purpose="LOGIN",
        otp_hash=hashlib.sha256(otp.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    token = api_client.post(
        "/api/v1/auth/verify-otp/",
        json={"phone": phone, "otp": otp, "purpose": "LOGIN"},
    ).json()["access_token"]

    response = api_client.get(
        "/api/v1/jobs/00000000-0000-0000-0000-000000000000/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
