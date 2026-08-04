"""
Auth endpoint tests — README section 11.2
"""
import pytest


@pytest.mark.django_db
def test_send_otp_valid_phone(api_client):
    response = api_client.post(
        "/api/v1/auth/send-otp/",
        json={"phone": "9876543210", "purpose": "LOGIN"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["expires_in"] == 300


@pytest.mark.django_db
def test_send_otp_invalid_phone(api_client):
    response = api_client.post(
        "/api/v1/auth/send-otp/",
        json={"phone": "1234567890", "purpose": "LOGIN"},
    )
    assert response.status_code == 422


@pytest.mark.django_db
def test_send_otp_invalid_purpose(api_client):
    response = api_client.post(
        "/api/v1/auth/send-otp/",
        json={"phone": "9876543210", "purpose": "INVALID"},
    )
    assert response.status_code == 422


@pytest.mark.django_db
def test_verify_otp_invalid(api_client):
    response = api_client.post(
        "/api/v1/auth/verify-otp/",
        json={"phone": "9876543210", "otp": "000000", "purpose": "LOGIN"},
    )
    assert response.status_code == 400
    assert "OTP" in response.json()["detail"]


@pytest.mark.django_db
def test_verify_otp_valid(api_client):
    import hashlib
    from django.utils import timezone
    from datetime import timedelta
    from apps.accounts.models import OTPChallenge

    phone = "9812345678"
    otp = "123456"
    OTPChallenge.objects.create(
        phone=phone,
        purpose="LOGIN",
        otp_hash=hashlib.sha256(otp.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    response = api_client.post(
        "/api/v1/auth/verify-otp/",
        json={"phone": phone, "otp": otp, "purpose": "LOGIN"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.django_db
def test_refresh_token_invalid(api_client):
    response = api_client.post(
        "/api/v1/auth/refresh/",
        json={"refresh_token": "invalid.token.here"},
    )
    assert response.status_code == 401
