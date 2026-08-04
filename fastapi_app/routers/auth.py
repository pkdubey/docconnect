import hashlib
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer()


class OTPRequest(BaseModel):
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    purpose: str = Field(..., pattern=r'^(LOGIN|REGISTER|RESET_PASSWORD)$')


class OTPVerify(BaseModel):
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    otp: str = Field(..., min_length=6, max_length=6)
    purpose: str = Field(default='LOGIN')
    device_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/send-otp/")
async def send_otp(request: OTPRequest):
    from django.utils import timezone
    from datetime import timedelta
    from apps.accounts.models import OTPChallenge
    from apps.core.services.sms import send_otp_sms

    # Limit resends: max 5 in last 10 minutes
    recent = OTPChallenge.objects.filter(
        phone=request.phone,
        purpose=request.purpose,
        created_at__gte=timezone.now() - timedelta(minutes=10),
    ).count()
    if recent >= 5:
        raise HTTPException(status_code=429, detail="Too many OTP requests. Try after 10 minutes.")

    otp = str(secrets.randbelow(900000) + 100000)
    otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    OTPChallenge.objects.create(
        phone=request.phone,
        purpose=request.purpose,
        otp_hash=otp_hash,
        expires_at=timezone.now() + timedelta(seconds=300),
    )
    await send_otp_sms(request.phone, otp)
    return {"success": True, "message": "OTP sent", "expires_in": 300}


@router.post("/verify-otp/", response_model=TokenResponse)
async def verify_otp(request: OTPVerify):
    from django.utils import timezone
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import RefreshToken
    from apps.accounts.models import OTPChallenge

    challenge = OTPChallenge.objects.filter(
        phone=request.phone,
        purpose=request.purpose,
        consumed_at__isnull=True,
        expires_at__gt=timezone.now(),
    ).order_by('-created_at').first()

    if not challenge:
        raise HTTPException(status_code=400, detail="No valid OTP found")

    if challenge.attempts >= challenge.max_attempts:
        raise HTTPException(status_code=400, detail="Max OTP attempts exceeded")

    if challenge.otp_hash != hashlib.sha256(request.otp.encode()).hexdigest():
        challenge.attempts += 1
        challenge.save(update_fields=['attempts'])
        raise HTTPException(status_code=400, detail="Invalid OTP")

    challenge.consumed_at = timezone.now()
    challenge.save(update_fields=['consumed_at'])

    User = get_user_model()
    user, created = User.objects.get_or_create(
        phone=request.phone,
        defaults={'user_type': 'DOCTOR', 'status': 'ACTIVE'},
    )
    refresh = RefreshToken.for_user(user)
    return TokenResponse(access_token=str(refresh.access_token), refresh_token=str(refresh))


@router.post("/refresh/", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest):
    from rest_framework_simplejwt.tokens import RefreshToken as RT
    from rest_framework_simplejwt.exceptions import TokenError
    try:
        refresh = RT(body.refresh_token)
        return TokenResponse(access_token=str(refresh.access_token), refresh_token=str(refresh))
    except TokenError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout/")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError
    try:
        token = AccessToken(credentials.credentials)
        token.blacklist()
    except (TokenError, Exception):
        pass
    return {"success": True, "message": "Logged out"}
