from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    from rest_framework_simplejwt.tokens import AccessToken
    from django.contrib.auth import get_user_model

    try:
        token = AccessToken(credentials.credentials)
        User = get_user_model()
        user = User.objects.get(id=token['user_id'])
        if user.status != 'ACTIVE':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not active")
        return user
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
    try:
        return current_user.doctor_profile
    except DoctorProfile.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")
