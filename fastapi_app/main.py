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

app = FastAPI(
    title="DocConnect API",
    description=(
        "Verified Professional Network for Doctors\n\n"
        "## Authentication\n"
        "1. Call `POST /api/v1/auth/login/` with phone + password\n"
        "2. Copy the `access_token` from the response\n"
        "3. Click **Authorize 🔒** (top right) → paste token → click Authorize\n"
        "4. All protected endpoints will now work"
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
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
