import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docconnect_backend.settings.development')
django.setup()

from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from a2wsgi import WSGIMiddleware

from fastapi_app.routers import auth, doctors, hospitals, jobs, availability, shifts, messaging, notifications, feed
from fastapi_app.middleware.logging import LoggingMiddleware

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
app.include_router(doctors.router)
app.include_router(hospitals.router)
app.include_router(jobs.router)
app.include_router(availability.router)
app.include_router(shifts.router)
app.include_router(messaging.router)
app.include_router(notifications.router)
app.include_router(feed.router)


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Mount Django — handles /admin/, /static/, and landing page
from docconnect_backend.wsgi import application as django_wsgi
app.mount("/", WSGIMiddleware(django_wsgi))
