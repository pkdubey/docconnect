import hashlib
import secrets
from typing import Optional

from asgiref.sync import sync_to_async
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
    user_type: str = Field(default='DOCTOR', pattern=r'^(DOCTOR|HOSPITAL_ADMIN)$')
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
    from django.conf import settings
    from datetime import timedelta
    from apps.accounts.models import OTPChallenge

    def _check_and_create():
        recent = OTPChallenge.objects.filter(
            phone=request.phone,
            purpose=request.purpose,
            created_at__gte=timezone.now() - timedelta(minutes=10),
        ).count()
        if recent >= 5:
            return None, "rate_limited"
        otp = str(secrets.randbelow(900000) + 100000)
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        OTPChallenge.objects.create(
            phone=request.phone,
            purpose=request.purpose,
            otp_hash=otp_hash,
            expires_at=timezone.now() + timedelta(seconds=300),
        )
        return otp, "ok"

    otp, result = await sync_to_async(_check_and_create, thread_sensitive=True)()
    if result == "rate_limited":
        raise HTTPException(status_code=429, detail="Too many OTP requests. Try after 10 minutes.")

    response: dict = {"success": True, "message": "OTP sent", "expires_in": 300}

    if getattr(settings, 'DEBUG', False) or not getattr(settings, 'SMS_API_KEY', ''):
        response["otp"] = otp
        response["message"] = "OTP generated (SMS disabled in dev mode)"
    else:
        from apps.core.services.sms import send_otp_sms
        try:
            await send_otp_sms(request.phone, otp)
        except Exception:
            pass

    return response


@router.post("/verify-otp/", response_model=TokenResponse)
async def verify_otp(request: OTPVerify):
    from django.utils import timezone
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import RefreshToken
    from apps.accounts.models import OTPChallenge

    def _verify_and_get_tokens():
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
        user, _ = User.objects.get_or_create(
            phone=request.phone,
            defaults={'user_type': request.user_type, 'status': 'ACTIVE'},
        )
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token), str(refresh)

    try:
        access_token, refresh_token = await sync_to_async(_verify_and_get_tokens, thread_sensitive=True)()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh/", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest):
    from rest_framework_simplejwt.tokens import RefreshToken as RT
    from rest_framework_simplejwt.exceptions import TokenError

    def _refresh():
        refresh = RT(body.refresh_token)
        return str(refresh.access_token), str(refresh)

    try:
        access_token, new_refresh = await sync_to_async(_refresh, thread_sensitive=True)()
        return TokenResponse(access_token=access_token, refresh_token=new_refresh)
    except TokenError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout/")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError

    def _blacklist():
        try:
            token = AccessToken(credentials.credentials)
            token.blacklist()
        except (TokenError, Exception):
            pass

    await sync_to_async(_blacklist, thread_sensitive=True)()
    return {"success": True, "message": "Logged out"}
