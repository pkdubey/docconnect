"""
Super Admin MFA / TOTP endpoints.

Flow:
  1. POST /api/v1/auth/mfa/setup/       → returns otpauth_uri + secret (scan with authenticator app)
  2. POST /api/v1/auth/mfa/verify/      → confirm TOTP code to activate MFA
  3. POST /api/v1/auth/mfa/login/       → after password login, submit TOTP code to get tokens
  4. POST /api/v1/auth/mfa/disable/     → Super Admin disables MFA (requires TOTP confirmation)

pyotp is used for TOTP generation/verification (RFC 6238).
"""
from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth/mfa", tags=["MFA / 2FA"])


class MFASetupOut(BaseModel):
    otpauth_uri: str
    secret: str
    message: str


class TOTPVerify(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class MFALoginRequest(BaseModel):
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    password: str
    totp_code: str = Field(..., min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── 1. Setup MFA ──────────────────────────────────────────────

@router.post("/setup/", response_model=MFASetupOut, summary="Generate TOTP secret for MFA setup")
async def mfa_setup(current_user=Depends(get_current_user)):
    """
    Generates a new TOTP secret and returns the otpauth URI.
    Scan the URI with Google Authenticator / Authy.
    MFA is NOT active until confirmed via POST /mfa/verify/.
    """
    if current_user.user_type != 'ADMIN':
        raise HTTPException(status_code=403, detail="MFA is only available for Admin accounts")

    def _generate():
        try:
            import pyotp
        except ImportError:
            raise HTTPException(status_code=500, detail="pyotp not installed. Run: pip install pyotp")
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=current_user.phone,
            issuer_name="DocConnect"
        )
        # Store secret (not yet active — activated after verify)
        current_user.totp_secret = secret
        current_user.mfa_enabled = False
        current_user.save(update_fields=['totp_secret', 'mfa_enabled'])
        return secret, uri

    try:
        secret, uri = await sync_to_async(_generate, thread_sensitive=True)()
    except HTTPException:
        raise
    return MFASetupOut(
        otpauth_uri=uri,
        secret=secret,
        message="Scan the QR code with your authenticator app, then confirm with POST /mfa/verify/"
    )


# ── 2. Verify & Activate MFA ──────────────────────────────────

@router.post("/verify/", summary="Confirm TOTP code to activate MFA")
async def mfa_verify(body: TOTPVerify, current_user=Depends(get_current_user)):
    """Verifies the TOTP code and activates MFA on the account."""
    if current_user.user_type != 'ADMIN':
        raise HTTPException(status_code=403, detail="MFA is only available for Admin accounts")

    def _verify():
        try:
            import pyotp
        except ImportError:
            raise HTTPException(status_code=500, detail="pyotp not installed")
        if not current_user.totp_secret:
            raise HTTPException(status_code=400, detail="MFA not set up. Call POST /mfa/setup/ first")
        totp = pyotp.TOTP(current_user.totp_secret)
        if not totp.verify(body.code, valid_window=1):
            raise HTTPException(status_code=400, detail="Invalid TOTP code")
        current_user.mfa_enabled = True
        current_user.save(update_fields=['mfa_enabled'])

    try:
        await sync_to_async(_verify, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "mfa_enabled": True, "message": "MFA activated successfully"}


# ── 3. MFA Login ──────────────────────────────────────────────

@router.post("/login/", response_model=TokenResponse, summary="Login with password + TOTP code")
async def mfa_login(body: MFALoginRequest):
    """
    For accounts with MFA enabled — submit phone + password + TOTP code in one step.
    Returns JWT tokens on success.
    """
    def _login():
        try:
            import pyotp
        except ImportError:
            raise HTTPException(status_code=500, detail="pyotp not installed")
        from django.contrib.auth import get_user_model
        from rest_framework_simplejwt.tokens import RefreshToken
        User = get_user_model()
        try:
            user = User.objects.get(phone=body.phone)
        except User.DoesNotExist:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user.check_password(body.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if user.status != 'ACTIVE':
            raise HTTPException(status_code=403, detail="Account not active")
        if not user.mfa_enabled or not user.totp_secret:
            raise HTTPException(status_code=400, detail="MFA not enabled on this account. Use /auth/login/")
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(body.totp_code, valid_window=1):
            raise HTTPException(status_code=400, detail="Invalid TOTP code")
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token), str(refresh)

    try:
        access_token, refresh_token = await sync_to_async(_login, thread_sensitive=True)()
    except HTTPException:
        raise
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# ── 4. Disable MFA ────────────────────────────────────────────

@router.post("/disable/", summary="Disable MFA (requires TOTP confirmation)")
async def mfa_disable(body: TOTPVerify, current_user=Depends(get_current_user)):
    """Disables MFA after confirming with a valid TOTP code."""
    if current_user.user_type != 'ADMIN':
        raise HTTPException(status_code=403, detail="MFA is only available for Admin accounts")

    def _disable():
        try:
            import pyotp
        except ImportError:
            raise HTTPException(status_code=500, detail="pyotp not installed")
        if not current_user.mfa_enabled or not current_user.totp_secret:
            raise HTTPException(status_code=400, detail="MFA is not enabled")
        totp = pyotp.TOTP(current_user.totp_secret)
        if not totp.verify(body.code, valid_window=1):
            raise HTTPException(status_code=400, detail="Invalid TOTP code")
        current_user.mfa_enabled = False
        current_user.totp_secret = None
        current_user.save(update_fields=['mfa_enabled', 'totp_secret'])

    try:
        await sync_to_async(_disable, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "mfa_enabled": False, "message": "MFA disabled"}


# ── 5. MFA Status ─────────────────────────────────────────────

@router.get("/status/", summary="Get MFA status for current user")
async def mfa_status(current_user=Depends(get_current_user)):
    return {
        "mfa_enabled": current_user.mfa_enabled,
        "mfa_configured": bool(current_user.totp_secret),
    }
