from asgiref.sync import sync_to_async
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


def run_sync(func):
    """Wrap a sync callable for use in async context via sync_to_async."""
    return sync_to_async(func, thread_sensitive=True)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    from rest_framework_simplejwt.tokens import AccessToken
    from django.contrib.auth import get_user_model

    def _get_user():
        token = AccessToken(credentials.credentials)
        User = get_user_model()
        user = User.objects.get(id=token['user_id'])
        if user.status != 'ACTIVE':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not active")
        return user

    try:
        return await run_sync(_get_user)()
    except HTTPException:
        raise
    except (InvalidToken, TokenError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_doctor(current_user=Depends(get_current_user)):
    from apps.doctors.models import DoctorProfile
    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a doctor")

    def _get_profile():
        try:
            return current_user.doctor_profile
        except DoctorProfile.DoesNotExist:
            return None

    profile = await run_sync(_get_profile)()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")
    return profile
