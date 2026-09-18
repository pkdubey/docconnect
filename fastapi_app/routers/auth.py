import hashlib
import secrets
from typing import Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

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
    model_config = ConfigDict(json_schema_extra={"example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer"
    }})
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordLoginRequest(BaseModel):
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    password: str = Field(..., min_length=4)
    user_type: str = Field(default='DOCTOR', pattern=r'^(DOCTOR|HOSPITAL_ADMIN|ADMIN)$')
    device_id: Optional[str] = None


class RegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str = Field(..., min_length=1, max_length=80)
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    password: str = Field(..., min_length=8)
    user_type: str = Field(default='DOCTOR', pattern=r'^(DOCTOR|HOSPITAL_ADMIN|HOSPITAL_HR)$')
    email: Optional[str] = None


class OTPSendResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "success": True, "message": "OTP sent", "expires_in": 300, "otp": None
    }})
    success: bool
    message: str
    expires_in: int
    otp: Optional[str] = None


class LogoutResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"success": True, "message": "Logged out"}})
    success: bool
    message: str


class RegisterResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_type": "DOCTOR", "profile_created": True
    }})
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    user_type: str
    profile_created: bool


@router.post("/register/", response_model=RegisterResponse, status_code=201)
async def register(request: RegisterRequest):
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import RefreshToken

    def _register():
        User = get_user_model()
        if User.objects.filter(phone=request.phone).exists():
            raise HTTPException(status_code=409, detail="An account with this phone number already exists")
        if request.email and User.objects.filter(email=request.email).exists():
            raise HTTPException(status_code=409, detail="An account with this email already exists")

        user = User.objects.create_user(
            phone=request.phone,
            user_type=request.user_type,
            password=request.password,
            email=request.email or None,
        )
        user.metadata = {'first_name': request.first_name, 'last_name': request.last_name}
        user.save(update_fields=['metadata'])

        profile_created = False
        if request.user_type == 'DOCTOR':
            from apps.doctors.models import DoctorProfile
            DoctorProfile.objects.create(
                user=user,
                first_name=request.first_name,
                last_name=request.last_name,
            )
            profile_created = True

        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token), str(refresh), str(user.id), user.user_type, profile_created

    try:
        access_token, refresh_token, user_id, user_type, profile_created = await sync_to_async(_register, thread_sensitive=True)()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return RegisterResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user_id,
        user_type=user_type,
        profile_created=profile_created,
    )


@router.post("/login/", response_model=TokenResponse)
async def login_with_password(request: PasswordLoginRequest):
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import RefreshToken

    def _login():
        User = get_user_model()
        try:
            user = User.objects.get(phone=request.phone)
        except User.DoesNotExist:
            raise HTTPException(status_code=401, detail="Invalid phone or password")
        if not user.check_password(request.password):
            raise HTTPException(status_code=401, detail="Invalid phone or password")
        if user.status != 'ACTIVE':
            raise HTTPException(status_code=403, detail="Account is not active")
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token), str(refresh), user.user_type

    try:
        access_token, refresh_token, user_type = await sync_to_async(_login, thread_sensitive=True)()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/send-otp/", response_model=OTPSendResponse)
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

    return OTPSendResponse(**response)


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


@router.post("/logout/", response_model=LogoutResponse)
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
    return LogoutResponse(success=True, message="Logged out")


class ForgotPasswordRequest(BaseModel):
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')


class ResetPasswordRequest(BaseModel):
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


@router.post("/password/forgot/", response_model=OTPSendResponse)
async def forgot_password(request: ForgotPasswordRequest):
    import hashlib, secrets
    from django.utils import timezone
    from datetime import timedelta
    from apps.accounts.models import OTPChallenge
    from django.contrib.auth import get_user_model

    def _create_otp():
        User = get_user_model()
        if not User.objects.filter(phone=request.phone).exists():
            return None, "not_found"
        otp = str(secrets.randbelow(900000) + 100000)
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        OTPChallenge.objects.create(
            phone=request.phone, purpose='RESET_PASSWORD',
            otp_hash=otp_hash, expires_at=timezone.now() + timedelta(seconds=300),
        )
        return otp, "ok"

    otp, result = await sync_to_async(_create_otp, thread_sensitive=True)()
    if result == "not_found":
        # Return success to prevent phone enumeration
        return OTPSendResponse(success=True, message="If account exists, OTP sent", expires_in=300)

    from django.conf import settings
    response = {"success": True, "message": "OTP sent", "expires_in": 300}
    if getattr(settings, 'DEBUG', False) or not getattr(settings, 'SMS_API_KEY', ''):
        response["otp"] = otp
        response["message"] = "OTP generated (dev mode)"
    return OTPSendResponse(**response)


@router.post("/password/reset/", response_model=LogoutResponse)
async def reset_password(request: ResetPasswordRequest):
    import hashlib
    from django.utils import timezone
    from django.contrib.auth import get_user_model
    from apps.accounts.models import OTPChallenge

    def _reset():
        challenge = OTPChallenge.objects.filter(
            phone=request.phone, purpose='RESET_PASSWORD',
            consumed_at__isnull=True, expires_at__gt=timezone.now(),
        ).order_by('-created_at').first()
        if not challenge:
            raise HTTPException(status_code=400, detail="No valid OTP found")
        if challenge.otp_hash != hashlib.sha256(request.otp.encode()).hexdigest():
            challenge.attempts += 1
            challenge.save(update_fields=['attempts'])
            raise HTTPException(status_code=400, detail="Invalid OTP")
        challenge.consumed_at = timezone.now()
        challenge.save(update_fields=['consumed_at'])
        User = get_user_model()
        try:
            user = User.objects.get(phone=request.phone)
        except User.DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")
        user.set_password(request.new_password)
        user.save(update_fields=['password'])

    try:
        await sync_to_async(_reset, thread_sensitive=True)()
    except HTTPException:
        raise
    return LogoutResponse(success=True, message="Password reset successfully")


@router.post("/password/change/", response_model=LogoutResponse)
async def change_password(
    request: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError
    from django.contrib.auth import get_user_model

    def _change():
        try:
            token = AccessToken(credentials.credentials)
            user_id = token['user_id']
        except TokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.check_password(request.old_password):
            raise HTTPException(status_code=400, detail="Old password is incorrect")
        user.set_password(request.new_password)
        user.save(update_fields=['password'])

    try:
        await sync_to_async(_change, thread_sensitive=True)()
    except HTTPException:
        raise
    return LogoutResponse(success=True, message="Password changed successfully")


@router.get("/sessions/")
async def list_sessions(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError
    from apps.accounts.models import RefreshSession
    from django.utils import timezone

    def _list():
        try:
            token = AccessToken(credentials.credentials)
            user_id = token['user_id']
        except TokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        sessions = list(RefreshSession.objects.filter(
            user_id=user_id, revoked_at__isnull=True, expires_at__gt=timezone.now()
        ).order_by('-created_at'))
        return sessions

    try:
        sessions = await sync_to_async(_list, thread_sensitive=True)()
    except HTTPException:
        raise
    return {
        "sessions": [{"id": str(s.id), "device_name": s.device_name,
                      "ip_address": s.ip_address, "created_at": s.created_at.isoformat()} for s in sessions]
    }


@router.delete("/sessions/{session_id}/", response_model=LogoutResponse)
async def revoke_session(session_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError
    from apps.accounts.models import RefreshSession
    from django.utils import timezone

    def _revoke():
        try:
            token = AccessToken(credentials.credentials)
            user_id = token['user_id']
        except TokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        updated = RefreshSession.objects.filter(id=session_id, user_id=user_id).update(revoked_at=timezone.now())
        if not updated:
            raise HTTPException(status_code=404, detail="Session not found")

    try:
        await sync_to_async(_revoke, thread_sensitive=True)()
    except HTTPException:
        raise
    return LogoutResponse(success=True, message="Session revoked")


@router.post("/sessions/revoke-all/", response_model=LogoutResponse)
async def revoke_all_sessions(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError
    from apps.accounts.models import RefreshSession
    from django.utils import timezone

    def _revoke_all():
        try:
            token = AccessToken(credentials.credentials)
            user_id = token['user_id']
        except TokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        RefreshSession.objects.filter(user_id=user_id, revoked_at__isnull=True).update(revoked_at=timezone.now())

    try:
        await sync_to_async(_revoke_all, thread_sensitive=True)()
    except HTTPException:
        raise
    return LogoutResponse(success=True, message="All sessions revoked")


@router.delete("/account/", response_model=LogoutResponse, include_in_schema=False)
async def delete_account_auth_alias(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Alias — kept for backward compat. Use DELETE /api/v1/account/ instead."""
    return await _delete_account_impl(credentials)


async def _delete_account_impl(credentials: HTTPAuthorizationCredentials):
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError
    from django.contrib.auth import get_user_model

    def _delete():
        try:
            token = AccessToken(credentials.credentials)
            user_id = token['user_id']
        except TokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        User = get_user_model()
        User.objects.filter(id=user_id).update(status='DELETED', is_active=False)
        # Cascade: withdraw active job applications
        try:
            from apps.doctors.models import DoctorProfile
            from apps.jobs.models import JobApplication
            dp = DoctorProfile.objects.filter(user_id=user_id).first()
            if dp:
                JobApplication.objects.filter(
                    doctor=dp,
                    status__in=('APPLIED', 'PROFILE_VIEWED', 'SHORTLISTED', 'INTERVIEW', 'OFFERED')
                ).update(status='WITHDRAWN')
                # Deactivate availabilities
                from apps.availability.models import DoctorAvailability
                DoctorAvailability.objects.filter(doctor=dp, is_active=True).update(is_active=False)
                # Cancel pending shift requests
                from apps.shifts.models import ShiftRequest
                from django.utils import timezone
                ShiftRequest.objects.filter(
                    doctor=dp,
                    status__in=('REQUESTED', 'ACCEPTED_BY_DOCTOR')
                ).update(status='CANCELLED', cancelled_at=timezone.now())
        except Exception:
            pass

    try:
        await sync_to_async(_delete, thread_sensitive=True)()
    except HTTPException:
        raise
    return LogoutResponse(success=True, message="Account deactivated")
