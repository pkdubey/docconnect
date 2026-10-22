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

---

## ⚡ 3-Step Swagger Setup

**Step 1 — Login and get token:**
Go to **Authentication → POST /api/v1/auth/login/** → click **Try it out** → use test credentials below → **Execute**

Copy the `access_token` from the response.

**Step 2 — Authorize:**
Click **Authorize 🔒** button (top right of this page) → paste the `access_token` → click **Authorize** → **Close**.

**Step 3 — Call any endpoint:**
All 🔒 endpoints will now work. Click any endpoint → **Try it out** → **Execute**.

---

## 🧪 Test Credentials (Dev Only)

| Role | Phone | Password | Use for |
|------|-------|----------|---------|
| Doctor (Verified) | `9000000001` | `Test@1234` | All doctor APIs |
| Doctor (Verified) | `9000000002` | `Test@1234` | Testing connections/messaging |
| Hospital Admin | `8000000001` | `Test@1234` | All hospital/jobs APIs |
| Platform Admin | `9999999998` | `Test@1234` | Admin panel APIs |

> Login with `user_type: "DOCTOR"` for doctor accounts, `user_type: "HOSPITAL_ADMIN"` for hospital accounts.

---

## 📱 Doctor App — Screen-by-Screen API Flow

### 🚀 App Launch / Splash
```
If token stored → POST /auth/refresh/  →  go to Home
If no token     →  go to Login screen
```

### 📝 Register Screen
```
POST /auth/register/   { user_type: "DOCTOR" }  →  save access_token + refresh_token
```
After register → go to Profile Setup.

### 🔐 Login Screen
```
Option A (password):  POST /auth/login/
Option B (OTP):       POST /auth/send-otp/  →  POST /auth/verify-otp/
```
After login → call POST /devices/ to register push token (silent, background).

### 👤 Profile Setup (First Time Only)
```
1. GET  /masters/specialties/                        ← load specialty dropdown
2. GET  /masters/qualifications/                     ← load qualification dropdown
3. POST /doctors/profile/                            ← create profile
4. POST /doctors/profile/me/photo/                   ← upload photo (optional)
5. POST /doctors/profile/me/registrations/           ← add NMC number
6. POST /doctors/profile/me/verification/submit/     ← submit for verification
```

### 🏠 Home Screen  ← ONE API CALL
```
GET /feed/home/
→ returns: stats + urgent_jobs[] + suggested_doctors[] + unread_messages + unread_notifications + pending_connections
```
⚠️ Do NOT call multiple APIs for home. This single endpoint returns everything.

### 📰 Feed Screen
```
GET  /feed/?page=1                          ← load posts (infinite scroll)
POST /feed/posts/{id}/like/                 ← like/unlike toggle
GET  /feed/posts/{id}/comments/             ← load comments
POST /feed/posts/{id}/comments/             ← add comment (multipart/form-data)
POST /feed/comments/{id}/reply/             ← reply to comment
POST /feed/posts/                           ← create post (multipart/form-data)
```

### 💼 Jobs Screen
```
GET  /jobs/                                 ← browse jobs (filter: specialty, city, job_type, is_urgent)
GET  /jobs/{id}/                            ← job detail
POST /jobs/{id}/apply/                      ← one-tap apply
POST /jobs/{id}/save/                       ← save for later
GET  /doctors/me/saved-jobs/                ← saved jobs list
GET  /jobs/my-applications/                 ← my applications (filter by status)
POST /jobs/{id}/withdraw/                   ← withdraw application
```

### 🤝 Network Screen
```
GET  /network/connections/?type=accepted    ← My Connections tab
GET  /network/connections/?type=received    ← Pending Requests tab
POST /network/connections/request/          ← send connection request
POST /network/connections/{id}/accept/      ← accept request
POST /network/connections/{id}/reject/      ← reject request
```

### 💬 Messages Screen
```
GET  /messages/conversations/               ← list all chats
GET  /messages/conversations/{id}/messages/ ← open a chat
POST /messages/conversations/{id}/messages/ ← send message
POST /messages/conversations/{id}/read/     ← mark as read (call on open)
POST /messages/conversations/              ← start new chat { participant_user_id }
```

### 🔔 Notifications Screen
```
GET  /notifications/                        ← list notifications
GET  /notifications/unread-count/           ← badge count (call on app resume)
PATCH /notifications/{id}/read/             ← mark one read
POST /notifications/read-all/              ← mark all read
```

### 📅 Availability Screen (Locum/Visiting)
```
POST /availability/                                  ← post availability with slots[]
GET  /availability/me/                               ← my availabilities
GET  /shifts/requirements/?urgency=IMMEDIATE         ← browse urgent shifts
POST /shifts/requirements/{id}/request/              ← request a shift
GET  /shifts/requests/mine/                          ← my shift requests
PATCH /shifts/requests/{id}/respond/  { accept: true } ← accept/decline shift
```

---

## 🏥 Hospital App — Screen-by-Screen API Flow

### 🏥 Hospital Setup
```
1. POST /auth/register/          { user_type: "HOSPITAL_ADMIN" }
2. POST /hospitals/register/     ← create hospital profile
3. POST /hospitals/me/verification/submit/
4. POST /hospitals/me/departments/
5. POST /hospitals/me/invite-user/   ← add HR/Recruiter
```

### 📊 Dashboard
```
GET /analytics/hospital/    ← jobs, applications, hired, shifts stats
GET /feed/home/             ← unread counts
```

### 📋 Post a Job
```
1. GET  /masters/specialties/       ← dropdown
2. GET  /masters/qualifications/    ← dropdown
3. POST /jobs/                      ← create job (auto-published)
```

### 👥 Recruitment Pipeline
```
GET  /jobs/{id}/applications/                    ← view applicants
PATCH /jobs/applications/{id}/status/            ← move pipeline: SHORTLISTED → INTERVIEW → OFFERED → HIRED
POST /applications/{id}/interview/               ← schedule interview
POST /applications/{id}/offer/                   ← send offer
POST /applications/{id}/notes/                   ← add internal HR note
```

### 🔍 Candidate Discovery
```
GET  /hospitals/me/candidates/?specialty=uuid&city=Mumbai&verified_only=true
GET  /jobs/{id}/matches/    ← AI matched doctors for a job
```

### ⚡ Urgent Shifts
```
POST /shifts/requirements/                           ← post urgent requirement
GET  /shifts/requirements/{id}/matched-doctors/      ← see matched doctors
POST /shifts/requirements/{id}/request/              ← send shift request to doctor
PATCH /shifts/requests/{id}/confirm/                 ← confirm after doctor accepts
PATCH /shifts/requests/{id}/complete/                ← mark completed
```

---

## 🔄 Token Refresh Logic (Mobile)

```
On any 401 response:
  → POST /auth/refresh/  with stored refresh_token
  → If success: save new access_token, retry original request
  → If 401 again: clear tokens, redirect to Login screen
```

---

## 📤 File Uploads

```
Step 1: POST /files/upload/   (multipart, purpose: CV / PROFILE_PHOTO / CREDENTIAL)
        → returns file_id
Step 2: Use file_id in other APIs (e.g. cv_file_id when applying to job)
Step 3: GET /files/{id}/signed-url/  → get temporary URL to display the file
```

---

## ❌ Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| `400` | Validation error | Show `detail` message to user |
| `401` | Token expired | Refresh token → retry |
| `403` | Wrong role | Show "Access denied" |
| `404` | Not found | Show "Not found" |
| `409` | Conflict (duplicate) | Show conflict message |
| `429` | Rate limited | Wait and retry |
| `500` | Server error | Log and show generic error |

Error body is always: `{ "detail": "message here" }`

---

## 📄 Pagination

All list endpoints: `?page=1&page_size=20`
Response always has: `total`, `page`, `page_size`, `results[]`
For infinite scroll: keep loading until `results` is empty.

---

## 🏷️ API Groups

| Tag | What it covers |
|-----|----------------|
| **Authentication** | Register, Login, OTP, Token refresh, Sessions, Password |
| **Feed & Posts** | Home screen (1 call), post feed, create/like/comment |
| **Network** | Connections, follow, block, reports |
| **Doctors** | Profile, qualifications, experience, verification, privacy |
| **Jobs** | Post jobs, apply, pipeline, saved jobs, recommendations |
| **Applications** | Interview, offer, notes, invite (hospital side) |
| **Hospitals** | Register hospital, branches, departments, staff, candidates |
| **Availability** | Doctor availability slots and preferences |
| **Shifts** | Urgent shift requirements, requests, full lifecycle |
| **Messaging** | Conversations, messages, read receipts, block/report |
| **Notifications** | List, unread count, mark read, preferences |
| **Devices** | Register FCM/APNs token for push notifications |
| **Search** | Universal search across doctors/hospitals/jobs/communities |
| **Communities** | Specialty groups, join/leave, community posts |
| **Files** | Upload files, get signed URLs |
| **Masters** | Specialties, qualifications, job types — load once, cache |
| **Support** | Raise and reply to support tickets |
| **Admin** | Platform admin — verification, moderation, users, audit |

---

## 📅 Date Format
All timestamps: ISO 8601 → `2025-08-15T10:30:00Z`
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
