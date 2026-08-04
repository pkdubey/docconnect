"""
Auth middleware — attaches current user to request state for logging/tracing.
Actual auth enforcement is done via Depends(get_current_user) in each router.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        if token:
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                from django.contrib.auth import get_user_model
                access_token = AccessToken(token)
                User = get_user_model()
                user = User.objects.get(id=access_token['user_id'])
                request.state.user = user
            except Exception:
                request.state.user = None
        else:
            request.state.user = None

        return await call_next(request)
