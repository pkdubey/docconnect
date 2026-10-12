import os
import django

# Respect whatever DJANGO_SETTINGS_MODULE was set before import (e.g. test settings).
# Only fall back to development if nothing is set.
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'docconnect_backend.settings.development'

# Only call setup() if Django hasn't been configured yet (avoids double-setup in tests).
from django.apps import apps as _django_apps
if not _django_apps.ready:
    django.setup()

from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from a2wsgi import WSGIMiddleware

from fastapi_app.routers import (
    auth, doctors, hospitals, jobs, availability, shifts,
    messaging, notifications, feed, network, search, communities, admin, devices,
    files, masters, support, billing, mfa,
    cme, endorsements, second_opinions, analytics, telemedicine
)
from fastapi_app.middleware.logging import LoggingMiddleware
from fastapi import APIRouter as _APIRouter, Depends as _Depends
from fastapi.security import HTTPBearer as _HTTPBearer, HTTPAuthorizationCredentials as _HTTPAuthCreds
_account_security = _HTTPBearer()
_account_router = _APIRouter(prefix="/api/v1", tags=["Account"])


@_account_router.delete("/account/")
async def delete_account(credentials: _HTTPAuthCreds = _Depends(_account_security)):
    return await auth._delete_account_impl(credentials)

_DESCRIPTION = """
# DocConnect API — Verified Professional Network for Doctors

## Quick Start for Mobile Developers

### Step 1 — Get a Token
```
POST /api/v1/auth/login/
Content-Type: application/json

{ "phone": "9000000001", "password": "Test@1234" }
```
Response gives you `access_token` (valid 60 min) and `refresh_token` (valid 7 days).

### Step 2 — Authorize in Swagger
Click **Authorize 🔒** (top right) → paste `access_token` → click Authorize.
All protected endpoints will now work.

### Step 3 — Refresh Token
```
POST /api/v1/auth/refresh/
{ "refresh": "<refresh_token>" }
```

---

## Test Credentials (Dev Only)

| Role | Phone | Password |
|------|-------|----------|
| Doctor (Verified) | `9000000001` | `Test@1234` |
| Doctor (Verified) | `9000000002` | `Test@1234` |
| Hospital Admin | `8000000001` | `Test@1234` |
| Platform Admin | `9999999998` | `Test@1234` |

---

## API Groups

| Tag | What it covers |
|-----|----------------|
| **Auth** | Register, Login, OTP, Token refresh, Sessions |
| **Feed & Posts** | Home screen, post feed, create/like/comment |
| **Network** | Connections, follow, block, reports |
| **Doctors** | Profile, qualifications, experience, verification |
| **Jobs** | Post jobs, apply, pipeline, saved jobs |
| **Hospitals** | Register hospital, branches, departments, staff |
| **Availability** | Doctor availability slots |
| **Shifts** | Urgent shift requirements, requests, lifecycle |
| **Messaging** | Conversations, messages, read receipts |
| **Notifications** | List, unread count, mark read, preferences |
| **Search** | Universal search across doctors/hospitals/jobs |
| **Communities** | Specialty groups, join/leave, community posts |
| **Masters** | Specialties, qualifications, job types (lookup lists) |
| **Admin** | Platform admin — verification, moderation, users |

---

## Common Response Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `400` | Validation error — check `detail` field |
| `401` | Token missing or expired — re-login |
| `403` | Forbidden — wrong user type or suspended |
| `404` | Resource not found |
| `500` | Server error — report to backend team |

---

## Pagination

All list endpoints support `?page=1&page_size=10`.
Response always includes `has_more: true/false` — keep fetching until `has_more` is `false`.

## Date Format
All timestamps are ISO 8601: `2025-08-15T10:30:00Z`
"""

app = FastAPI(
    title="DocConnect API",
    description=_DESCRIPTION,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 3,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True,
    },
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste your access_token from /api/v1/auth/login/",
        }
    }
    for path in schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(_account_router)
app.include_router(jobs.applications_router)
app.include_router(doctors.router)
app.include_router(hospitals.router)
app.include_router(jobs.router)
app.include_router(availability.router)
app.include_router(shifts.router)
app.include_router(messaging.router)
app.include_router(notifications.router)
app.include_router(notifications.notif_prefs_router)
app.include_router(feed.router)
app.include_router(network.router)
app.include_router(network.reports_router)
app.include_router(search.router)
app.include_router(communities.router)
app.include_router(admin.router)
app.include_router(devices.router)
app.include_router(files.router)
app.include_router(masters.router)
app.include_router(support.router)
app.include_router(billing.router)
app.include_router(mfa.router)
app.include_router(cme.router)
app.include_router(endorsements.router)
app.include_router(second_opinions.router)
app.include_router(analytics.router)
app.include_router(telemedicine.router)


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Mount Django — handles /admin/, /static/, and landing page
from docconnect_backend.wsgi import application as django_wsgi
app.mount("/", WSGIMiddleware(django_wsgi))
