import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docconnect_backend.settings.development')
django.setup()

from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from a2wsgi import WSGIMiddleware

from fastapi_app.routers import auth, doctors, hospitals, jobs, availability, shifts, messaging, notifications
from fastapi_app.middleware.logging import LoggingMiddleware

app = FastAPI(
    title="DocConnect API",
    description="Verified Professional Network for Doctors",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

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


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Mount Django — handles /admin/, /static/, and landing page
from docconnect_backend.wsgi import application as django_wsgi
app.mount("/", WSGIMiddleware(django_wsgi))
