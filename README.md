# DocConnect — Verified Professional Network for Doctors

> LinkedIn for Doctors — Verified identities, doctor-only jobs, clinical networking & locum marketplace.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python) ![Django](https://img.shields.io/badge/Django-5.0+-green?logo=django) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal?logo=fastapi) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue?logo=postgresql) ![Redis](https://img.shields.io/badge/Redis-7.2+-red?logo=redis) ![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker) ![License](https://img.shields.io/badge/License-Proprietary-red)

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Module 1 & 2 — Doctor Professional Network](#2-module-1--doctor-professional-network)
3. [Module 3 — Doctor Career Marketplace](#3-module-2--doctor-career-marketplace)
4. [Module 4 — Doctor Availability Exchange](#4-module-3--doctor-availability-exchange)
5. [Module 5 — Platform Operations (Admin CRM)](#5-module-5--platform-operations-admin-crm)
6. [Module 6 — Doctor Mobile App](#6-module-6--doctor-mobile-app)
7. [Backend, Database & API Specification (Spec 02)](#7-backend-database--api-specification-spec-02)
8. [API Global Contract](#8-api-global-contract)
9. [System Architecture](#9-system-architecture)
10. [Technology Stack](#10-technology-stack)
11. [Database Design](#11-database-design)
12. [API Architecture (FastAPI)](#12-api-architecture-fastapi)
13. [Project Structure](#13-project-structure)
14. [Development Setup](#14-development-setup)
15. [Deployment](#15-deployment)
16. [API Documentation](#16-api-documentation)
17. [Security](#17-security)
18. [Testing](#18-testing)
19. [Troubleshooting](#19-troubleshooting)
20. [Roadmap](#20-roadmap)
21. [Gap Audit Final Report](#21-gap-audit-final-report-doc-connect-backend-gap-audit)
22. [Contributing](#22-contributing)

---

## 1. Project Overview

### 1.1 What is DocConnect?

DocConnect is a verified professional network exclusively for doctors. It provides a LinkedIn-style platform purpose-built for MBBS/MD/MS professionals with features including:

- **Verified Identity** - NMC + State Medical Council registration checked at sign-up
- **Doctor-only Jobs** - Hospitals & clinics post full-time, locum & consultant roles
- **Clinical Networking** - Case discussions, referrals, second opinions among peers
- **CME & Compliance** - Track continuing-education credits required for license renewal
- **Availability Exchange** - Structured locum and part-time marketplace

### 1.2 Core Modules

| Module | Description | Section |
|--------|-------------|--------|
| **Module 1 — Identity, Onboarding & Verification** | Doctor registration/verification, hospital onboarding, branches, staff roles | [Section 2](#2-module-1--doctor-professional-network) |
| **Module 2 — Professional Network & Community** | LinkedIn-style verified profiles, connections, feed, specialty communities, messaging | [Section 2](#2-module-1--doctor-professional-network) |
| **Module 3 — Career Marketplace & Recruitment** | Hospital job posting, one-tap apply, recruitment CRM, AI matching | [Section 3](#3-module-2--doctor-career-marketplace) |
| **Module 4 — Availability Exchange & Workforce** | Doctor availability, urgent shift requirements, doctor matching, shift lifecycle | [Section 4](#4-module-3--doctor-availability-exchange) |
| **Module 5 — Platform Operations** | Admin CRM, moderation, reports, support, audit, analytics, billing | [Section 5](#5-module-5--platform-operations-admin-crm) |
| **Module 6 — Doctor Mobile App** | Navigation, onboarding, profile, networking rules, feed safety, jobs, availability, edge cases | [Section 6](#6-module-6--doctor-mobile-app) |

### 1.3 Actors & Target Users

| Actor | Core Responsibility | Access Domain |
|-------|--------------------|--------------|
| **Doctor** | Professional identity, network, jobs, applications, availability, shifts, messaging | Own data + permitted public/network/career data |
| **Hospital Admin** | Organization, branches, users, jobs, candidates, applications, urgent workforce | Own hospital/branch data + permitted doctor data |
| **HR / Recruiter** | Recruitment workflow and candidate operations | Assigned hospital scope |
| **Branch User** | Branch-scoped recruitment/workforce operations | Assigned branch scope |
| **Platform Admin** | Verification, moderation, reports, restrictions, communities, jobs, support, audit | Platform-wide, privileged |
| **Super Admin** | Platform configuration and irreversible/high-risk actions | Highest privileged scope |

### 1.4 Why Django 5.0+ with FastAPI?

```
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐          ┌────────────────────────┐   │
│  │    Django 5.0+   │          │       FastAPI          │   │
│  │  (Admin, ORM,    │◄────────►│  (High-Performance     │   │
│  │   Models, Auth)  │          │   REST API Layer)      │   │
│  └──────────────────┘          └────────────────────────┘   │
│                                                             │
│  • PostgreSQL 16+ with advanced features                    │
│  • Async support for high-performance APIs                  │
│  • Automatic OpenAPI/Swagger documentation                  │
│  • Type safety with Pydantic                                │
│  • Django Admin for content management                      │
│  • Django ORM for database operations                       │
└─────────────────────────────────────────────────────────────┘
```

### 1.5 Quick Start (TL;DR)

```bash
git clone https://github.com/pkdubey/docconnect.git && cd docconnect
cp .env.example .env

# Create & activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run migrations & seed data
python manage.py makemigrations accounts doctors hospitals jobs availability shifts messaging notifications
python manage.py migrate
python scripts/seed_data.py

# Start FastAPI server
python run.py
```

**URLs after startup:**

| Service | URL |
|---------|-----|
| API Swagger Docs | http://localhost:8000/api/docs |
| API ReDoc | http://localhost:8000/api/redoc |
| Django Admin | http://localhost:8000/admin |
| Health Check | http://localhost:8000/health |

**Super Admin Credentials (⚠️ LOCAL DEVELOPMENT ONLY):**

| Field | Value |
|-------|-------|
| Phone | `9999999999` |
| Password | `admin123` |
| User Type | `ADMIN` |

> ⚠️ **NEVER use these credentials in production.** Production deployments must use randomly generated credentials passed via `--phone` and `--password` CLI args or environment variables. The deployment pipeline must NOT call `create_admin.py` with default values.

> To create a Platform Admin (dev):
> ```bash
> python scripts/create_admin.py
> ```
> To create a Super Admin (dev):
> ```bash
> python scripts/create_admin.py --super
> ```
> To create a Super Admin (production — always pass explicit credentials):
> ```bash
> DJANGO_ENV=production python scripts/create_admin.py --phone <phone> --password <strong_password> --super
> ```

---

## 2. Module 1 — Doctor Professional Network

> LinkedIn-style verified professional network exclusively for doctors — profiles, connections, feed & specialty communities.

### 2.1 Doctor Profile (LinkedIn-style)

```
┌─────────────────────────────────────────────────────────────────┐
│                     DOCTOR PROFILE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  BANNER  (gradient / custom image)                       │   │
│  │  ┌──────┐  Dr. Arjun Sharma                              │   │
│  │  │ 👨‍⚕️   │  Cardiologist · 12 yrs exp                     │   │
│  │  │ Photo│  AIIMS Delhi · Mumbai                          │   │
│  │  └──────┘  ✅ NMC Verified  🟢 Open to Opportunities    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  About          Qualifications      Experience                  │
│  Specialization Clinical Interests  Registrations               │
│  Connections    Posts & Activity    Availability Badge          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Profile Fields:**

| Field | Description |
|-------|-------------|
| `first_name` / `last_name` | Doctor's full name |
| `headline` | 160-char tagline (e.g. "Cardiologist · AIIMS Delhi · 12 yrs") |
| `about` | Rich bio / summary |
| `photo_file_id` | Profile photo stored on AWS S3 |
| `primary_specialization_id` | Linked to `Specialization` master table |
| `clinical_interests` | Array of UUID refs to specializations |
| `professional_location` | JSONB — city, state, pincode, coordinates |
| `experience_years` | Decimal (e.g. 12.5) |
| `open_to_opportunities` | Boolean — shows availability badge |
| `profile_visibility` | `EVERYONE` / `DOCTORS_ONLY` / `CONNECTIONS_ONLY` |
| `career_visibility` | `VERIFIED_HOSPITALS` / `SELECTED_HOSPITALS` / `HIDDEN` |

### 2.2 Verification System

```
  UNVERIFIED ──▶ PENDING ──▶ VERIFIED
                    │
                    └──▶ REJECTED (with reason)
                              │
                              └──▶ RESUBMISSION (controlled resubmit)
```

| Step | Action |
|------|--------|
| 1 | Doctor submits NMC / State Council registration number |
| 2 | System stores `DoctorRegistration` with `council_id` + `registration_number` |
| 3 | Admin verifies via Django Admin panel |
| 4 | Status moves to `VERIFIED` — green badge appears on profile |
| 5 | Rejected profiles get `verification_rejected_reason` |

**Supported Councils:** NMC, MCI, Maharashtra MC, Delhi MC, Karnataka MC, Tamil Nadu MC (extensible via `Council` master table)

**Doctor Qualifications tracked:**
- Degree (MBBS / MD / MS / DM / MCh / DNB / BDS / MDS / BAMS / BHMS)
- Institution name
- Passing year
- Specialization

**Doctor Experience tracked:**
- Role / Designation
- Hospital name & location
- Start date / End date / Is current
- Description

### 2.3 Connections & Feed

| Feature | Status | Description |
|---------|--------|-------------|
| Doctor Search | ✅ Live | Full-text search by name, specialty, city, experience |
| Profile View | ✅ Live | View any verified doctor's profile |
| Visibility Controls | ✅ Live | Control who sees your profile & career info |
| Open to Opportunities | ✅ Live | Toggle availability badge visible to hospitals |
| Feed / Posts | ✅ Live | Create posts (UPDATE/CASE/ARTICLE/PHOTO), like, comment, reply |
| Connections | ✅ Live | Send / accept / decline / withdraw connection requests |
| Home Summary | ✅ Live | Single API — stats, urgent jobs, suggested doctors, unread counts |
| Hospital Follow | ✅ Live | Doctors can follow hospital pages |
| Endorsements | 🔜 Phase 3 | Peer skill endorsements |

### 2.4 Specialty Communities

| Feature | Status | Description |
|---------|--------|-------------|
| Specialty Groups | ✅ Phase 2 | Cardiology, Neurology, Pediatrics etc. — moderator APIs implemented |
| Case Discussions | ✅ Live | Anonymised clinical case sharing via CASE post type |
| Second Opinions | 🔜 Phase 3 | Request peer review on complex cases |
| CME Events | 🔜 Phase 3 | Continuing Medical Education tracking |

### 2.5 Messaging

```
Doctor A ──▶ Start Conversation ──▶ Doctor B
                    │
              Message Types:
              • TEXT
              • IMAGE
              • DOCUMENT
              • SHIFT_REQUEST (linked to shift)
              • JOB_REFERRAL (linked to job)
```

**API Endpoints — Network Module:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register/` | Register with phone + password |
| POST | `/api/v1/auth/login/` | Login with phone + password |
| POST | `/api/v1/auth/send-otp/` | Send OTP to phone |
| POST | `/api/v1/auth/verify-otp/` | Verify OTP and get tokens |
| POST | `/api/v1/auth/refresh/` | Refresh JWT token |
| POST | `/api/v1/auth/logout/` | Logout / blacklist token |
| POST | `/api/v1/auth/password/forgot/` | Forgot password — send reset challenge |
| POST | `/api/v1/auth/password/reset/` | Reset password with token |
| POST | `/api/v1/auth/password/change/` | Change password (authenticated) |
| GET | `/api/v1/auth/sessions/` | List active sessions / devices |
| DELETE | `/api/v1/auth/sessions/{id}/` | Revoke a specific session |
| POST | `/api/v1/auth/sessions/revoke-all/` | Revoke all sessions |
| DELETE | `/api/v1/account/` | Deactivate / delete account |
| POST | `/api/v1/doctors/profile/` | Create doctor profile |
| GET | `/api/v1/doctors/profile/me/` | Get my profile |
| PATCH | `/api/v1/doctors/profile/me/` | Update my profile |
| GET | `/api/v1/doctors/profile/{id}/` | View any doctor's profile |
| POST | `/api/v1/doctors/profile/me/photo/` | Upload profile photo |
| GET | `/api/v1/doctors/search/` | Search doctors (name/specialty/city/exp) |
| POST | `/api/v1/doctors/profile/me/registrations/` | Add NMC registration |
| GET | `/api/v1/doctors/profile/me/registrations/` | List my registrations |
| POST | `/api/v1/doctors/profile/me/qualifications/` | Add qualification |
| GET | `/api/v1/doctors/profile/me/qualifications/` | List qualifications |
| DELETE | `/api/v1/doctors/profile/me/qualifications/{id}/` | Delete qualification |
| POST | `/api/v1/doctors/profile/me/experiences/` | Add experience |
| GET | `/api/v1/doctors/profile/me/experiences/` | List experiences |
| PATCH | `/api/v1/doctors/profile/me/experiences/{id}/` | Update experience |
| DELETE | `/api/v1/doctors/profile/me/experiences/{id}/` | Delete experience |
| POST | `/api/v1/doctors/profile/me/affiliations/` | Add hospital affiliation |
| GET | `/api/v1/doctors/profile/me/affiliations/` | List affiliations |
| PATCH | `/api/v1/doctors/profile/me/affiliations/{id}/` | Update affiliation |
| DELETE | `/api/v1/doctors/profile/me/affiliations/{id}/` | Delete affiliation |
| GET | `/api/v1/doctors/profile/me/verification/` | Get verification status |
| POST | `/api/v1/doctors/profile/me/verification/submit/` | Submit verification documents |
| POST | `/api/v1/doctors/profile/me/verification/resubmit/` | Resubmit after rejection |
| GET | `/api/v1/doctors/profile/me/status/` | Get professional status |
| PUT | `/api/v1/doctors/profile/me/status/` | Update professional status |
| GET | `/api/v1/doctors/profile/me/privacy/` | Get privacy settings |
| PUT | `/api/v1/doctors/profile/me/privacy/` | Update privacy settings |
| POST | `/api/v1/files/upload/` | Upload file (photo/CV/credential) |
| GET | `/api/v1/files/{id}/` | Get file metadata |
| GET | `/api/v1/files/{id}/signed-url/` | Get expiring signed URL for file |
| DELETE | `/api/v1/files/{id}/` | Delete file |
| GET | `/api/v1/search/doctors/` | Search doctors (advanced filters) |
| GET | `/api/v1/search/hospitals/` | Search hospitals |
| GET | `/api/v1/search/jobs/` | Search jobs |
| GET | `/api/v1/search/communities/` | Search specialty communities |
| GET | `/api/v1/search/universal/` | Universal search (doctors/hospitals/jobs/communities) |
| POST | `/api/v1/network/connections/request/` | Send connection request |
| POST | `/api/v1/network/connections/{id}/accept/` | Accept connection |
| POST | `/api/v1/network/connections/{id}/reject/` | Reject connection |
| DELETE | `/api/v1/network/connections/{id}/` | Remove connection |
| GET | `/api/v1/network/connections/` | List connections / requests |
| POST | `/api/v1/network/follow/{user_id}/` | Follow a user |
| DELETE | `/api/v1/network/follow/{user_id}/` | Unfollow a user |
| POST | `/api/v1/network/block/{user_id}/` | Block a user |
| DELETE | `/api/v1/network/block/{user_id}/` | Unblock a user |
| GET | `/api/v1/network/blocked/` | List blocked users |
| POST | `/api/v1/reports/` | Report a profile/post/comment/job/hospital |
| GET | `/api/v1/feed/home/` | Home summary (stats, urgent jobs, suggested doctors) |
| GET | `/api/v1/feed/` | Paginated feed posts |
| POST | `/api/v1/feed/posts/` | Create a post (text/image/case/article) |
| PATCH | `/api/v1/feed/posts/{id}/` | Edit own post |
| DELETE | `/api/v1/feed/posts/{id}/` | Delete own post |
| POST | `/api/v1/feed/posts/{id}/like/` | Like / unlike a post |
| GET | `/api/v1/feed/posts/{id}/comments/` | Get comments for a post |
| POST | `/api/v1/feed/posts/{id}/comments/` | Add a comment |
| PATCH | `/api/v1/feed/comments/{id}/` | Edit own comment / reply |
| DELETE | `/api/v1/feed/comments/{id}/` | Delete own comment / reply |
| POST | `/api/v1/feed/comments/{id}/reply/` | Reply to a comment |
| GET | `/api/v1/communities/` | List specialty communities |
| GET | `/api/v1/communities/{id}/` | Community detail |
| POST | `/api/v1/communities/{id}/join/` | Join community |
| DELETE | `/api/v1/communities/{id}/leave/` | Leave community |
| GET | `/api/v1/communities/{id}/posts/` | Community posts |
| POST | `/api/v1/communities/{id}/posts/` | Post in community |
| POST | `/api/v1/messages/conversations/` | Start a conversation |
| GET | `/api/v1/messages/conversations/` | List my conversations |
| GET | `/api/v1/messages/conversations/{id}/messages/` | Get messages |
| POST | `/api/v1/messages/conversations/{id}/messages/` | Send a message |
| POST | `/api/v1/messages/conversations/{id}/read/` | Mark conversation as read |
| POST | `/api/v1/messages/conversations/{id}/report/` | Report conversation |
| POST | `/api/v1/messages/conversations/{id}/block/` | Block conversation |
| DELETE | `/api/v1/messages/conversations/{id}/block/` | Unblock conversation |
| POST | `/api/v1/devices/` | Register device for push notifications |
| DELETE | `/api/v1/devices/{id}/` | Revoke device token |
| GET | `/api/v1/notifications/` | List notifications (paginated) |
| GET | `/api/v1/notifications/unread-count/` | Get unread notification count |
| PATCH | `/api/v1/notifications/{id}/read/` | Mark notification as read |
| POST | `/api/v1/notifications/read-all/` | Mark all notifications as read |
| GET | `/api/v1/notification-preferences/` | Get per-event notification preferences |
| PUT | `/api/v1/notification-preferences/` | Update notification preferences |

---

## 3. Module 2 — Doctor Career Marketplace

> Hospital-side job posting + doctor-side one-tap apply + full recruitment CRM pipeline + AI matching (Phase 2).

### 3.0 Hospital / HR CRM

**CRM Purpose:** The hospital CRM is the recruitment and workforce operating console. It lets verified healthcare institutions discover doctors, publish jobs, manage applicants and source urgent/temporary coverage.

**CRM Main Menu:**

| Menu | Functions |
|------|-----------|
| Dashboard | Active jobs, new applicants, shortlisted doctors, interviews, urgent requirements |
| Hospital Profile | Profile, branches, departments, facilities, verification |
| Users & Roles | Owner/Admin, HR/Recruiter, branch-level access |
| Jobs | Create/edit/publish/close, applicants, status management |
| Candidates | Search doctors, filters, profile view, shortlist, notes, communication |
| Applications | Pipeline, interview, offer/hire/reject/withdraw |
| Availability Exchange | Urgent requirements, matched doctors, requests, confirmations |
| Messages | Doctor/hospital professional conversations |
| Notifications | Recruitment and workforce alerts |
| Reports/Analytics | Hiring funnel, jobs, candidate activity, workforce metrics |
| Billing | Plan, limits, invoices, subscription — if activated |
| Settings | Privacy, notification preferences, organization settings |

**CRM Permission Matrix:**

| Action | Hospital Admin | HR/Recruiter | Branch User |
|--------|---------------|--------------|-------------|
| Edit organization profile | Yes | Configurable | No/limited |
| Manage users | Yes | No | No |
| Create jobs | Yes | Yes | Configurable |
| View candidates | Yes | Yes | Assigned/branch scope |
| Change application status | Yes | Yes | Configurable |
| Create urgent requirement | Yes | Yes | Configurable |
| Billing | Yes | No | No |
| Audit logs | Yes | Limited | No |

> Exact permissions must be finalized before backend RBAC implementation.

### 3.1 Hospital Onboarding

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Admin   │──▶│  OTP     │──▶│ Hospital │──▶│ Branches │──▶│ Verified │
│  Phone   │   │  Verify  │   │ Details  │   │  Depts   │   │ Hospital │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

**Hospital Profile Fields:**

| Field | Description |
|-------|-------------|
| `name` | Hospital / Clinic name |
| `type` | `HOSPITAL` / `CLINIC` / `NURSING_HOME` / `MEDICAL_COLLEGE` |
| `location` | JSONB — address, city, state, pincode, coordinates |
| `bed_count` | Number of beds |
| `verification_status` | `UNVERIFIED` → `PENDING` → `VERIFIED` |
| `logo_file_id` | Logo stored on AWS S3 |

**Hospital Structure:**
```
Hospital
  └── Branches (multiple locations)
        └── Departments (Cardiology, ICU, OPD...)
              └── Staff (ADMIN / HR / RECRUITER roles)
```

### 3.2 Job Posting

**Job Creation Fields:**

| Field | Description |
|-------|-------------|
| `title` | Job title / role |
| `department_id` | Linked department |
| `qualification_ids` | Required qualifications |
| `specialty_id` | Required specialization |
| `experience_min_years` | Minimum experience required |
| `location` | JSONB — city, state, pincode, coordinates |
| `salary_min` / `salary_max` | Salary range |
| `salary_visibility` | `PUBLIC` / `ON_REQUEST` / `HIDDEN` |
| `shift_type` | `DAY` / `NIGHT` / `ROTATIONAL` / `FLEXIBLE` |
| `joining_requirement` | Joining date / notice period |
| `job_type` | `FULL_TIME` / `PART_TIME` / `VISITING` / `LOCUM` / `CONTRACT` |
| `description` | Full job description |
| `positions` | Number of openings |
| `is_urgent` | Boolean — shows urgent badge |
| `closing_date` | Application deadline / auto-expire date |
| `status` | `DRAFT` → `PUBLISHED` → `CLOSED` / `EXPIRED` / `FILLED` |

### 3.2a Candidate Discovery Filters

Hospital HR can search and filter doctors using:

- Qualification
- Specialization
- Experience (years)
- Location / city / state
- Verified doctor only
- Professional status
- Available now
- Locum availability
- Visiting consultant availability
- Distance / radius (km)

### 3.2b Candidate Actions

| Action | Description |
|--------|-------------|
| View profile | View allowed professional profile fields per privacy settings |
| Shortlist | Add doctor to shortlist for a job |
| Reject | Mark candidate as not suitable |
| Move pipeline | Move through APPLIED → SHORTLISTED → INTERVIEW → OFFERED → HIRED |
| Send message | Send professional message via messaging module |
| Invite to opportunity | Invite doctor to apply for a specific job |
| Add internal notes | Add HR-only notes on candidate (stored in application metadata) |
| Record interview outcome | Update interview result (PASS/FAIL/PENDING) |
| Issue offer / mark hired | Send offer letter details, mark as HIRED on acceptance |

### 3.3 Job Application Pipeline (Recruitment CRM)

```
  APPLIED
    │
    ▼
  PROFILE_VIEWED  ◀── Hospital HR views doctor profile
    │
    ▼
  SHORTLISTED     ◀── Added to shortlist
    │
    ▼
  INTERVIEW       ◀── Interview scheduled
    │
    ├──▶ OFFERED  ◀── Offer letter sent
    │       │
    │       └──▶ HIRED ◀── Doctor accepts offer
    │
    └──▶ REJECTED

  (Doctor can WITHDRAW at any stage)
```

Every status change is logged in `ApplicationHistory` with:
- `from_status` / `to_status`
- `changed_by` (user who made the change)
- `notes` (optional reason)

### 3.3a Urgent Requirement Workflow

```
1. Hospital creates ShiftRequirement
   (specialty, qualification, date, start/end time,
    location, compensation, doctors_required, urgency, notes)
        │
        ▼
2. System finds eligible available doctors
   (matches availability type, date, location, compensation)
        │
        ▼
3. HR reviews matching candidates list
        │
        ▼
4. Hospital sends ShiftRequest to selected doctor
        │
        ▼
5. Doctor accepts / declines
        │
        ▼
6. Hospital confirms (CONFIRMED_BY_HOSPITAL)
        │
        ▼
7. Shift completed or cancelled
   (all state changes timestamped and auditable)
```

### 3.4 AI Matching

> **Important:** Per the V2 specification, matching weights are NOT hardcoded. They are product-approved configuration values stored in `matching_configs` table. The factors below are the V1 matching inputs — weights must be approved before production use.

```
┌─────────────────────────────────────────────────────────────┐
│                    MATCHING ENGINE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  V1 Matching Factors (weights = configurable):              │
│  • verification status                                      │
│  • specialization match                                     │
│  • qualification match                                      │
│  • experience (years)                                       │
│  • date availability                                        │
│  • time availability                                        │
│  • location / distance                                      │
│  • preferred radius                                         │
│  • job type preference                                      │
│  • professional status                                      │
│                                                             │
│  Output: match_score + score_components[] + reasons[]       │
│  Config: versioned via matching_configs table               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**API Endpoints — Career Marketplace:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/hospitals/register/` | Register new hospital |
| GET | `/api/v1/hospitals/me/` | Get my hospital profile |
| PATCH | `/api/v1/hospitals/me/` | Update hospital profile |
| POST | `/api/v1/hospitals/me/verification/submit/` | Submit hospital verification documents |
| GET | `/api/v1/hospitals/me/verification/` | Get hospital verification status |
| POST | `/api/v1/hospitals/me/branches/` | Add hospital branch |
| GET | `/api/v1/hospitals/me/branches/` | List branches |
| PATCH | `/api/v1/hospitals/me/branches/{id}/` | Update branch |
| DELETE | `/api/v1/hospitals/me/branches/{id}/` | Deactivate branch |
| POST | `/api/v1/hospitals/me/departments/` | Add department |
| GET | `/api/v1/hospitals/me/departments/` | List departments |
| POST | `/api/v1/hospitals/me/users/` | Add hospital user (HR/Recruiter/Branch User) |
| GET | `/api/v1/hospitals/me/users/` | List hospital users |
| PATCH | `/api/v1/hospitals/me/users/{id}/` | Update user role/branch/status |
| DELETE | `/api/v1/hospitals/me/users/{id}/` | Revoke user membership |
| POST | `/api/v1/hospitals/me/invite-user/` | Invite HR / Recruiter |
| GET | `/api/v1/hospitals/me/staff/` | List hospital staff |
| POST | `/api/v1/hospitals/me/upload-logo/` | Upload hospital logo |
| GET | `/api/v1/hospitals/{id}/` | View public hospital profile |
| POST | `/api/v1/jobs/` | Create job posting (auto-published) |
| PATCH | `/api/v1/jobs/{id}/` | Update job posting |
| POST | `/api/v1/jobs/{id}/publish/` | Publish a draft job |
| POST | `/api/v1/jobs/{id}/close/` | Close a job posting |
| GET | `/api/v1/jobs/` | List jobs (specialty/city/type/search/urgent filters) |
| GET | `/api/v1/jobs/{id}/` | Get job details |
| POST | `/api/v1/jobs/{id}/save/` | Save a job |
| DELETE | `/api/v1/jobs/{id}/save/` | Unsave a job |
| GET | `/api/v1/doctors/me/saved-jobs/` | List saved jobs |
| GET | `/api/v1/jobs/my-applications/` | Doctor's applications (with status filter) |
| POST | `/api/v1/jobs/{id}/apply/` | One-tap apply |
| POST | `/api/v1/jobs/{id}/withdraw/` | Withdraw application |
| GET | `/api/v1/jobs/{id}/applications/` | Hospital — view applicants |
| PATCH | `/api/v1/jobs/applications/{id}/status/` | Update application status (logs history) |
| POST | `/api/v1/applications/{id}/notes/` | Add internal note to application |
| GET | `/api/v1/applications/{id}/notes/` | List application notes |
| POST | `/api/v1/applications/{id}/interview/` | Schedule interview |
| PATCH | `/api/v1/applications/{id}/interview/{interview_id}/` | Update interview outcome |
| POST | `/api/v1/applications/{id}/offer/` | Send offer |
| POST | `/api/v1/applications/{id}/invite/` | Invite doctor to apply |
| GET | `/api/v1/jobs/{id}/matches/` | Get matched doctors for a job |
| GET | `/api/v1/doctors/me/job-recommendations/` | Get recommended jobs for doctor |
| GET | `/api/v1/masters/specialties/` | List specialties |
| GET | `/api/v1/masters/qualifications/` | List qualifications |
| GET | `/api/v1/masters/job-types/` | List job types |
| GET | `/api/v1/masters/shift-types/` | List shift types |

---

## 4. Module 3 — Doctor Availability Exchange

> Structured locum & part-time marketplace — doctors post availability, hospitals post urgent requirements, system matches & manages full shift lifecycle.

### 4.1 Doctor Availability

```
┌─────────────────────────────────────────────────────────────┐
│               DOCTOR AVAILABILITY POSTING                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Dr. Priya Mehta — Anesthesiologist                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Type:     LOCUM                                    │    │
│  │  From:     15 Aug 2025  →  30 Aug 2025              │    │
│  │  Location: Mumbai, Maharashtra  (50 km radius)      │    │
│  │  Min Pay:  ₹8,000 / shift                           │    │
│  │  Slots:    Mon 09:00–17:00  |  Wed 09:00–17:00      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Availability Types:**

| Type | Description |
|------|-------------|
| `LOCUM` | Short-term fill-in shifts |
| `VISITING` | Regular visiting consultant slots |
| `TEMPORARY` | Fixed-term contract (weeks/months) |
| `PART_TIME` | Ongoing part-time engagement |

**Availability Slots** — each availability can have multiple time slots:
- `slot_date` — specific date
- `start_time` / `end_time` — time window
- `is_booked` — auto-updated when shift is confirmed

### 4.2 Urgent Hospital Requirement

```
┌─────────────────────────────────────────────────────────────┐
│              HOSPITAL SHIFT REQUIREMENT                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Apollo Hospital, Mumbai — ICU Department                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Specialty:   Anesthesiology                        │    │
│  │  Date:        18 Aug 2025                           │    │
│  │  Time:        08:00 – 20:00  (12 hr shift)          │    │
│  │  Doctors:     2 required                            │    │
│  │  Pay:         ₹12,000 / shift                       │    │
│  │  Urgency:     🔴 IMMEDIATE                         │     │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Urgency Levels:**

| Level | Description |
|-------|-------------|
| `NORMAL` | Standard requirement, planned in advance |
| `URGENT` | Required within 24–48 hours |
| `IMMEDIATE` | Required today / emergency fill |

**Requirement Status Flow:**
```
  OPEN ──▶ FILLED
    │
    ├──▶ CANCELLED
    └──▶ EXPIRED  (auto after requirement_date passes)
```

### 4.3 Doctor Matching

```
┌─────────────────────────────────────────────────────────────┐
│                   MATCHING ALGORITHM                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Hospital posts ShiftRequirement                            │
│           │                                                 │
│           ▼                                                 │
│  System filters DoctorAvailability where:                   │
│    • availability_type matches requirement type             │
│    • available_from ≤ requirement_date ≤ available_until    │
│    • preferred_location within preferred_radius_km          │
│    • minimum_compensation ≤ requirement compensation        │
│    • slot exists for requirement date & time                │
│           │                                                 │
│           ▼                                                 │
│  Matched doctors list returned to hospital                  │
│  Hospital sends ShiftRequest to selected doctors            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 Shift Lifecycle

```
  Hospital creates ShiftRequirement (status: OPEN)
           │
           ▼
  Hospital sends ShiftRequest to matched doctor
           │                    (status: REQUESTED)
           ▼
  Doctor responds:
    ├──▶ ACCEPTED_BY_DOCTOR
    │         │
    │         ▼
    │    Hospital confirms:
    │         ├──▶ CONFIRMED_BY_HOSPITAL
    │         │         │
    │         │         ▼
    │         │    Shift completed:
    │         │         └──▶ COMPLETED
    │         │
    │         └──▶ (Hospital ignores → doctor can cancel)
    │
    └──▶ DECLINED_BY_DOCTOR

  Either party can CANCEL at any stage
```

**Shift Request Status Reference:**

| Status | Triggered By | Description |
|--------|-------------|-------------|
| `REQUESTED` | Hospital | Hospital sends request to doctor |
| `ACCEPTED_BY_DOCTOR` | Doctor | Doctor accepts the shift |
| `DECLINED_BY_DOCTOR` | Doctor | Doctor declines |
| `CONFIRMED_BY_HOSPITAL` | Hospital | Hospital confirms after doctor accepts |
| `COMPLETED` | Hospital | Shift successfully completed |
| `CANCELLED` | Either | Cancelled before completion |

**API Endpoints — Availability Exchange:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/availability/` | Doctor posts availability (with slots) |
| GET | `/api/v1/availability/me/` | List my availabilities |
| PATCH | `/api/v1/availability/{id}/` | Update availability |
| DELETE | `/api/v1/availability/{id}/` | Deactivate availability |
| GET | `/api/v1/availability/{id}/slots/` | List slots for an availability |
| POST | `/api/v1/availability/{id}/slots/` | Add slot to availability |
| PATCH | `/api/v1/availability/slots/{slot_id}/` | Update a slot |
| DELETE | `/api/v1/availability/slots/{slot_id}/` | Delete a slot |
| GET | `/api/v1/availability/preferences/` | Get availability preferences |
| PUT | `/api/v1/availability/preferences/` | Update availability preferences |
| POST | `/api/v1/shifts/requirements/` | Hospital posts shift requirement |
| GET | `/api/v1/shifts/requirements/` | List open shift requirements (urgency/city/specialty filters) |
| PATCH | `/api/v1/shifts/requirements/{id}/` | Update shift requirement |
| GET | `/api/v1/shifts/requirements/mine/` | Hospital's own requirements |
| POST | `/api/v1/shifts/requirements/{id}/match/` | Get matched doctors for a requirement |
| GET | `/api/v1/shifts/requirements/{id}/matched-doctors/` | Get matched doctors for a requirement |
| POST | `/api/v1/shifts/requirements/{id}/request/` | Doctor requests a shift |
| PATCH | `/api/v1/shifts/requests/{id}/respond/` | Doctor accepts / declines |
| PATCH | `/api/v1/shifts/requests/{id}/confirm/` | Hospital confirms shift |
| PATCH | `/api/v1/shifts/requests/{id}/complete/` | Hospital marks shift completed |
| PATCH | `/api/v1/shifts/requests/{id}/cancel/` | Cancel shift request (either party) |
| GET | `/api/v1/shifts/requests/{id}/history/` | Shift request state history |
| GET | `/api/v1/shifts/requests/mine/` | Doctor's shift requests |

---

## 5. Module 5 — Platform Operations (Admin CRM)

> Admin CRM for verification, moderation, reports, restrictions, support, audit & analytics.

### 5.1 Admin Capabilities

| Module | Admin Capabilities |
|--------|--------------------|
| Overview | Doctors, hospitals, verified accounts, jobs, applications, urgent requirements, reports, active users |
| Doctor Verification | Queue, document review, approve/reject with reason, resubmission control, waiting time |
| Hospital Verification | Organization review, documents, approve/reject, branches |
| User Management | Search, view, restrict, suspend, restore, deactivate — reason required, audit logged |
| Moderation | Posts/comments/reports — patient privacy concerns, misinformation flags, harassment, reason required |
| Communities | Create/edit/archive specialty communities, manage moderators (✅ Phase 2 implemented) |
| Jobs | Monitor jobs, remove policy-violating jobs, investigate suspicious activity |
| Reports | Case queue, severity, evidence, resolution, escalation |
| Support | User tickets/issues and internal admin notes |
| Audit | Sensitive actions, verification decisions, restrictions, content removals — immutable log |
| Billing | Plans, entitlements, subscriptions, invoices/refunds (feature-flagged) |
| Settings | Specialties, qualifications, status values, configurable matching weights |

### 5.2 Verification SOP

| Step | Action |
|------|--------|
| 1 | Receive submission — doctor/hospital submits registration details & documents |
| 2 | Validate required fields and documents are present |
| 3 | Check registration information using the approved verification process |
| 4 | Approve or reject with mandatory reason |
| 5 | Record reviewer, timestamp and evidence in `AuditLog` |
| 6 | Notify user of outcome via in-app + push notification |
| 7 | Allow controlled resubmission for rejected cases |

### 5.2a Moderation Reason Codes

- `PATIENT_PRIVACY_CONCERN`
- `POTENTIAL_MEDICAL_MISINFORMATION`
- `SPAM`
- `HARASSMENT`
- `COPYRIGHT_CONCERN`
- `FAKE_DOCTOR_FALSE_CREDENTIALS`
- `PROFESSIONAL_MISCONDUCT_CONCERN`
- `OTHER_POLICY_VIOLATION`

### 5.2b Admin Safety Controls

- Two-step confirmation for irreversible actions (deactivate/delete)
- Reason required for all rejection / suspension / removal actions (400 if missing)
- Every privileged action writes an immutable `AuditLog` entry (`performed_by`, `target_type`, `target_id`, `metadata`)
- Role check on every admin endpoint — 403 if `user_type != ADMIN`
- Role separation between reviewer and super-admin for high-risk actions
- Private access to credential documents — signed URLs only, never public
- Export controls for sensitive data
- Search and filters across all case queues
- Internal support notes (`is_internal=True`) are hidden from end users
- Report severity levels: `LOW` / `MEDIUM` / `HIGH` / `CRITICAL`
- Matching config activation deactivates all other versions atomically

### 5.3 Report Lifecycle

```
  SUBMITTED ──▶ UNDER_REVIEW ──▶ ACTIONED
                    │
                    ├──▶ DISMISSED
                    └──▶ ESCALATED
```

**Report Model Fields:**

| Field | Description |
|-------|-------------|
| `reporter` | User who filed the report |
| `target_type` | `PROFILE` / `POST` / `COMMENT` / `JOB` / `HOSPITAL` |
| `target_id` | UUID of the reported object |
| `reason` | One of the 8 reason codes above |
| `severity` | `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` |
| `status` | `SUBMITTED` → `UNDER_REVIEW` → `ACTIONED` / `DISMISSED` / `ESCALATED` |
| `reviewed_by` | Admin who actioned the report |
| `resolution_notes` | Admin notes on resolution |
| `resolved_at` | Timestamp of resolution |

### 5.3a Support Ticket Model

| Field | Description |
|-------|-------------|
| `user` | Ticket owner |
| `subject` / `description` | Ticket content |
| `category` | `GENERAL` / `VERIFICATION` / `BILLING` / `TECHNICAL` |
| `status` | `OPEN` → `IN_PROGRESS` → `RESOLVED` / `CLOSED` |
| `assigned_to` | Admin assigned to ticket |
| `resolved_at` | Timestamp of resolution |
| `messages` | Thread of `SupportMessage` records |
| `is_internal` | Admin-only internal notes hidden from user |

### 5.3b Matching Config

```
  MatchingConfig
  ├── version       (e.g. "v1", "v2") — unique
  ├── weights       JSONB — {"specialization_match": 0.3, "experience": 0.2, ...}
  ├── is_active     only one config active at a time
  ├── approved_by   admin who created/approved
  └── description   optional notes
```

### 5.3c Operational Metrics (Analytics Overview)

| Metric | Description |
|--------|-------------|
| Doctor verification turnaround | Avg hours from submission to VERIFIED |
| Hospital verification turnaround | Avg hours from submission to VERIFIED |
| Verified doctors by specialty / location | Top 10 specialties with verified doctor counts |
| Active hospitals | Verified hospital count |
| Jobs posted / filled | Total, published, filled, urgent |
| Application funnel | Count per status: APPLIED → SHORTLISTED → INTERVIEW → OFFERED → HIRED |
| Urgent requirements filled | Count of IMMEDIATE/URGENT shift requirements with status FILLED |
| Shift acceptance rate | % of shift requests accepted by doctors |
| Shift completion rate | % of shift requests completed |
| Report resolution time | Avg hours from report submission to resolution |
| Network growth & active engagement | Total connections, accepted connections, active users |

### 5.4 Notification Event Matrix

| Event Code | Trigger | Recipients | Default Channels |
|------------|---------|------------|------------------|
| `CONNECTION_REQUEST` | New connection request | Target doctor | In-app + push |
| `CONNECTION_ACCEPTED` | Request accepted | Requester | In-app + push |
| `POST_INTERACTION` | Comment/reaction | Post owner | In-app + push |
| `NEW_MESSAGE` | New message | Recipient | In-app + push |
| `RECOMMENDED_JOB` | New/relevant job | Doctor | In-app + push |
| `APPLICATION_UPDATE` | Application status changes | Doctor | In-app + push |
| `INTERVIEW_UPDATE` | Interview created/updated | Doctor + HR | In-app + push |
| `SHIFT_REQUEST` | Hospital sends shift request | Doctor | In-app + push |
| `SHIFT_ACCEPTED` | Doctor accepts | Hospital/HR | In-app + push |
| `SHIFT_CONFIRMED` | Hospital confirms | Doctor | In-app + push |
| `SHIFT_CANCELLED` | Shift cancelled | Affected parties | In-app + push |
| `VERIFICATION_UPDATE` | Verification status changes | Account owner | In-app + push |
| `REPORT_UPDATE` | Report resolution | Reporter (policy-based) | In-app |
| `SUPPORT_UPDATE` | Support ticket response | Ticket requester | In-app + push/email |

### 5.5 API Endpoints — Admin CRM

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/dashboard/` | Platform overview metrics (includes open reports & tickets) |
| GET | `/api/v1/admin/doctors/verification-queue/` | Doctor verification queue (includes `waiting_hours`) |
| GET | `/api/v1/admin/doctors/verification-cases/{id}/` | Verification case detail |
| POST | `/api/v1/admin/doctors/verification-cases/{id}/approve/` | Approve doctor verification — writes AuditLog |
| POST | `/api/v1/admin/doctors/verification-cases/{id}/reject/` | Reject doctor verification — reason required, writes AuditLog |
| POST | `/api/v1/admin/doctors/verification-cases/{id}/resubmit/` | Allow resubmission — writes AuditLog |
| GET | `/api/v1/admin/hospitals/verification-queue/` | Hospital verification queue (includes `waiting_hours`) |
| POST | `/api/v1/admin/hospitals/verification-cases/{id}/approve/` | Approve hospital verification — writes AuditLog |
| POST | `/api/v1/admin/hospitals/verification-cases/{id}/reject/` | Reject hospital verification — reason required, writes AuditLog |
| GET | `/api/v1/admin/users/` | List all users (filter: user_type, status, search) |
| POST | `/api/v1/admin/users/{id}/restrict/` | Restrict user — reason required, writes AuditLog |
| POST | `/api/v1/admin/users/{id}/suspend/` | Suspend user — reason required, writes AuditLog |
| POST | `/api/v1/admin/users/{id}/restore/` | Restore user — reason required, writes AuditLog |
| POST | `/api/v1/admin/users/{id}/deactivate/` | Deactivate user — reason required, writes AuditLog |
| GET | `/api/v1/admin/reports/` | Reports queue (filter: status, severity, target_type) |
| GET | `/api/v1/admin/reports/{id}/` | Report detail |
| POST | `/api/v1/admin/reports/{id}/action/` | Action a report — writes AuditLog |
| POST | `/api/v1/admin/reports/{id}/dismiss/` | Dismiss a report — writes AuditLog |
| POST | `/api/v1/admin/reports/{id}/escalate/` | Escalate a report — writes AuditLog |
| POST | `/api/v1/admin/posts/{id}/moderate/` | Moderate a post — reason required, writes AuditLog |
| POST | `/api/v1/admin/jobs/{id}/moderate/` | Moderate a job — reason required, writes AuditLog |
| POST | `/api/v1/admin/communities/` | Create specialty community — writes AuditLog |
| PATCH | `/api/v1/admin/communities/{id}/` | Update community — writes AuditLog |
| POST | `/api/v1/admin/communities/{id}/archive/` | Archive community — writes AuditLog |
| GET | `/api/v1/admin/audit-logs/` | Audit log records (filter: action, target_type) |
| GET | `/api/v1/admin/analytics/overview/` | Full operational analytics (turnaround, funnel, shift rates, resolution time) |
| GET | `/api/v1/admin/support/tickets/` | Admin: list all tickets (filter: status, category) |
| PATCH | `/api/v1/admin/support/tickets/{id}/` | Update ticket status (admin) |
| POST | `/api/v1/admin/support/tickets/{id}/resolve/` | Resolve ticket |
| POST | `/api/v1/admin/support/tickets/{id}/messages/` | Admin reply or internal note on ticket — `is_internal` flag supported |
| GET | `/api/v1/admin/matching-configs/` | List all matching weight configs |
| POST | `/api/v1/admin/matching-configs/` | Create new matching config version |
| POST | `/api/v1/admin/matching-configs/{id}/activate/` | Activate a matching config (deactivates others) |
| POST | `/api/v1/admin/settings/specialties/` | Create specialty (admin) |
| PATCH | `/api/v1/admin/settings/specialties/{id}/` | Update specialty (admin) |
| POST | `/api/v1/admin/settings/qualifications/` | Create qualification (admin) |
| POST | `/api/v1/support/tickets/` | Create support ticket |
| GET | `/api/v1/support/tickets/` | List my support tickets (filter: status) |
| GET | `/api/v1/support/tickets/{id}/` | Ticket detail + messages (internal notes hidden) |
| POST | `/api/v1/support/tickets/{id}/messages/` | Add message to ticket |
| GET | `/api/v1/billing/plans/` | List billing plans |
| GET | `/api/v1/billing/subscription/` | Current hospital subscription |
| POST | `/api/v1/billing/subscription/` | Subscribe to a plan |
| PATCH | `/api/v1/billing/subscription/` | Update/cancel subscription |
| GET | `/api/v1/billing/invoices/` | List invoices |
| GET | `/api/v1/billing/invoices/{id}/` | Invoice detail |
| POST | `/api/v1/billing/webhooks/{provider}/` | Payment webhook (idempotent) |
| POST | `/api/v1/admin/billing/refunds/` | Issue refund |

---

## 6. Module 6 — Doctor Mobile App

> Android-native doctor app — verified professional identity, networking, jobs, availability exchange & clinical community.

### 6.1 Navigation Structure

| Area | Screens |
|------|---------|
| Onboarding | Splash, login, register, OTP/verification, credential submission, verification status |
| Home | Professional feed, recommended jobs, recommended doctors/communities, notifications |
| Network | Doctor search, filters, profile, connection requests, connections, following |
| Jobs | Recommended, nearby, urgent, saved, applied; job detail; apply; application tracker |
| Availability | Status, availability calendar, time slots, preferences, current/previous availability |
| Communities | Specialty list, community feed, posts, discussions |
| Messages | Conversation list, chat, attachments, professional context |
| Profile | Professional identity, experience, hospitals, qualifications, interests, privacy |
| Settings | Privacy, notifications, blocked users, account/security, support, logout |

### 6.2 Doctor Onboarding Flow

```
1. Create account (phone + password or OTP)
        │
        ▼
2. Complete professional identity
   (name, photo, headline, specialization, experience, location, languages)
        │
        ▼
3. Enter medical registration
   (registration number, medical council, registration year, documents)
        │
        ▼
4. Submit verification
        │
        ▼
5. Show verification state:
   ├─► PENDING  — awaiting admin review
   ├─► VERIFIED — green badge unlocked
   └─► REJECTED — reason shown + resubmission path
        │
        ▼
6. Until VERIFIED: restrict actions that require verified status
   (applying to jobs, posting availability, messaging hospitals)
```

**Verification-gated actions:**

| Action | Requires Verified |
|--------|------------------|
| Apply to jobs | Yes |
| Post availability | Yes |
| Message hospitals | Yes |
| Browse feed / posts | No |
| Search doctors | No |
| Send connection requests | No |

### 6.3 Professional Profile

| Field | Description |
|-------|-------------|
| `first_name` / `last_name` | Doctor's full name |
| `photo_file_id` | Profile photo (S3) |
| `headline` | 160-char tagline |
| `about` | Rich bio / summary |
| `primary_specialization_id` | Primary specialty |
| `clinical_interests` | Secondary specialties (array) |
| `experience_years` | Total experience (decimal) |
| `qualifications` | Degree, institution, year |
| `experiences` | Role, hospital, dates, is_current |
| `affiliations` | Current/previous hospital affiliations (JSONB) |
| `languages` | Spoken languages (e.g. `["English", "Hindi"]`) |
| `career_preferences` | Job type, location, salary preferences (JSONB) |
| `professional_location` | City, state, pincode, coordinates |
| `open_to_opportunities` | Availability badge for hospitals |
| `profile_visibility` | `EVERYONE` / `DOCTORS_ONLY` / `CONNECTIONS_ONLY` |
| `career_visibility` | `VERIFIED_HOSPITALS` / `SELECTED_HOSPITALS` / `HIDDEN` |
| `verification_status` | `UNVERIFIED` / `PENDING` / `VERIFIED` / `REJECTED` |

### 6.4 Networking Rules

| Relationship | Messaging Allowed | Profile Data Visible |
|--------------|------------------|---------------------|
| No relationship | No (doctors only after connection) | Name, headline, specialty, location per `profile_visibility` |
| Connection request sent/received | No | Same as above |
| Connected | Yes | Full professional profile |
| Blocked | No | Hidden |

> Messaging is only allowed between connected doctors. Hospitals can message doctors directly via the hospital CRM (professional context only).

### 6.5 Feed & Clinical Discussion Rules

- Post category must be selected from: `UPDATE` / `CASE` / `ARTICLE` / `PHOTO`
- `CASE` posts require `patient_privacy_confirmed = true` before submission
- PII auto-detection blocks posts containing: phone numbers, Aadhaar (12-digit), email addresses, patient IDs (PT\d+, IPD\d+)
- `pii_flagged = true` is set server-side if PII patterns are detected in non-CASE posts (flagged for moderation)
- Report and moderation controls available on every post and comment
- Feed remains professional — generic social content is subject to moderation

**PII patterns blocked/flagged:**

| Pattern | Example |
|---------|---------|
| Indian mobile number | `9876543210` |
| Aadhaar number | `123456789012` |
| Email address | `patient@gmail.com` |
| Patient ID | `PT001234`, `IPD/5678` |

### 6.6 Jobs & Application

```
Browse tabs:
  Recommended ── match_score + match_factors shown per job
  Nearby       ── filtered by professional_location
  Urgent       ── is_urgent = true
  Saved        ── doctor's saved_jobs list
  Applied      ── my-applications with status filter

Job Detail:
  └─ match_score (0–100) + match_factors breakdown
  └─ salary visibility: PUBLIC / ON_REQUEST / HIDDEN
  └─ what information is shared on apply (profile fields)

Apply:
  └─ One-tap apply uses professional profile
  └─ Optional CV attachment (file_id)
  └─ Confirmation screen shows exactly what is shared

Application Tracker:
  APPLIED → PROFILE_VIEWED → SHORTLISTED → INTERVIEW → OFFERED → HIRED
                                                                    └→ REJECTED
  Doctor can WITHDRAW at any stage before HIRED/REJECTED
```

**Match Score Factors (V1):**

| Factor | Weight |
|--------|--------|
| Specialization match | 40 pts |
| Experience ≥ required | 30 pts |
| Open to opportunities | 15 pts |
| Verified doctor | 15 pts |

### 6.7 Availability Exchange

```
Doctor sets availability:
  Type: LOCUM / VISITING / TEMPORARY / PART_TIME
  Dates: available_from → available_until
  Location: city + preferred_radius_km
  Min compensation: private (never shown publicly)
  Slots: date + start_time + end_time

Calendar rules:
  └─ Adding a slot checks for overlapping ACCEPTED/CONFIRMED shifts → 409 if conflict
  └─ Deactivating availability blocked if pending/confirmed shift requests exist

Shift request flow:
  Hospital sends request → Doctor accepts/declines → Hospital confirms → Completed
  Doctor can cancel before COMPLETED
  Hospital can cancel at any stage
```

### 6.8 Doctor-side Edge Cases

| Edge Case | Behaviour |
|-----------|----------|
| Verification rejected | Show rejection reason + resubmit button; restrict verified-only actions |
| Expired / invalid credential | Admin rejects with reason; doctor must resubmit updated documents |
| Hospital affiliation changed | Doctor updates affiliation via PATCH `/api/v1/doctors/profile/me/affiliations/{id}/` |
| Doctor changes status while application active | Application remains; doctor can withdraw; hospital sees updated status |
| Doctor deletes availability with active shift request | 409 — must cancel shift requests first |
| Overlapping shifts | 409 on slot creation and shift request if accepted/confirmed shift overlaps |
| Shift cancelled by hospital | ShiftRequest status → `CANCELLED`; doctor's slot `is_booked` reset; notification sent |
| Doctor blocks hospital/user | Blocked user hidden from feed/search; messaging disabled |
| Message/report abuse | Report submitted via `POST /api/v1/reports/`; conversation block via messaging endpoints |
| Document upload failure | `UPLOAD_INVALID` (400) with file type/size reason; retry allowed |
| Account deletion | User status → `DELETED`; active applications → `WITHDRAWN`; availabilities deactivated; pending shift requests → `CANCELLED` |

---

## 7. Backend, Database & API Specification (Spec 02)

> Source of truth for all backend decisions — entities, state machines, API groups, matching engine, privacy enforcement, security and API contract standards.

### 7.1 Backend Objective

Build a role-based platform API supporting Doctor, Hospital/HR and Platform Admin workflows. The backend is the authoritative source of truth for verification, privacy, matching, application, availability and shift states. All privacy rules are enforced at the query/serialization layer — hiding a field only in the UI is insufficient.

### 7.2 Core Entity Map

| Django App | Models / Tables |
|------------|-----------------|
| `accounts` | `users`, `otp_challenges`, `refresh_sessions` |
| `doctors` | `doctor_profiles`, `doctor_registrations`, `doctor_qualifications`, `doctor_experiences`, `doctor_affiliations`, `doctor_connections`, `follows`, `blocks`, `doctor_posts`, `post_likes`, `post_comments` |
| `hospitals` | `hospitals`, `hospital_branches`, `hospital_departments`, `hospital_users`, `hospital_follows` |
| `jobs` | `job_posts`, `job_applications`, `application_histories`, `job_saves` |
| `availability` | `doctor_availabilities`, `availability_slots` |
| `shifts` | `shift_requirements`, `shift_requests`, `shift_status_history` |
| `messaging` | `conversations`, `conversation_participants`, `messages` |
| `notifications` | `notifications`, `device_tokens`, `notification_preferences` |
| `core` | `specializations`, `qualifications`, `councils`, `communities`, `community_members`, `audit_logs`, `reports`, `report_evidence`, `support_tickets`, `support_messages`, `matching_configs`, `plans`, `subscriptions`, `entitlements`, `invoices`, `payments` |

### 7.3 State Machines

| Object | States |
|--------|--------|
| Doctor verification | `UNVERIFIED` → `PENDING` → `VERIFIED` / `REJECTED` → `RESUBMISSION` |
| Hospital verification | `UNVERIFIED` → `PENDING` → `VERIFIED` / `REJECTED` → `RESUBMISSION` |
| Job application | `APPLIED` → `PROFILE_VIEWED` → `SHORTLISTED` → `INTERVIEW` → `OFFERED` → `HIRED` / `REJECTED` / `WITHDRAWN` |
| Shift request | `REQUESTED` → `ACCEPTED_BY_DOCTOR` → `CONFIRMED_BY_HOSPITAL` → `COMPLETED` / `CANCELLED` |
| Professional status | `AVAILABLE_NOW` / `FULL_TIME` / `LOCUM` / `VISITING` / `PART_TIME` / `NOT_LOOKING` |
| Report | `SUBMITTED` → `UNDER_REVIEW` → `ACTIONED` / `DISMISSED` / `ESCALATED` |
| Subscription | `TRIALING` → `ACTIVE` → `PAST_DUE` → `CANCELLED` / `EXPIRED` |
| Invoice | `DRAFT` → `OPEN` → `PAID` / `VOID` / `UNCOLLECTIBLE` |
| Payment | `PENDING` → `CAPTURED` / `FAILED` → `REFUNDED` / `PARTIALLY_REFUNDED` |

### 7.4 API Groups & Responsibilities

| API Domain | Router File | Minimum Responsibility |
|------------|-------------|------------------------|
| Auth | `auth.py` | Register, login, OTP, refresh, logout, password reset, session/device management |
| Doctor | `doctors.py` | Profile CRUD, credentials, documents, verification, experiences, affiliations, professional status |
| Hospital | `hospitals.py` | Profile, branches, departments, verification, hospital users/roles |
| Discovery | `search.py` | Doctor search, hospital search, job search, community search, filters, pagination |
| Network | `network.py` | Connection request/accept/reject/remove, follow/unfollow, block/unblock |
| Feed | `feed.py` | Create/edit/delete post, comments, reactions, feed retrieval, PII detection, report |
| Community | `communities.py` | List, join/leave, posts, moderation |
| Jobs | `jobs.py` | Create/publish/close, save, apply, application status, candidate shortlist |
| Matching | `jobs.py` | Job→doctor matches and doctor→job recommendations with transparent score breakdown |
| Availability | `availability.py` | Calendar/slots, preferences, matching, urgent requirements |
| Shift | `shifts.py` | Request, accept/decline, confirm, complete, cancel, status history |
| Messaging | `messaging.py` | Conversations, messages, attachments, read receipts, block/report |
| Notifications | `notifications.py` | List, read, preferences, push token registration |
| Admin | `admin.py` | Verification queues, moderation, reports, user restrictions, communities, jobs, audit logs |
| Billing | `billing.py` | Plans, subscriptions, entitlements, invoices, payment webhooks |
| Support | `support.py` | Tickets, messages, internal notes |
| Masters | `masters.py` | Specialties, qualifications, councils, job/shift types |
| Files | `files.py` | Upload, signed URLs, delete |

### 7.5 Matching Engine — V1 Rules

Weights are **not hardcoded**. They are product-approved values stored in the `matching_configs` table (`MatchingConfig` model). The backend must not invent production weights without product approval.

```
Matching Factors (weights = configurable via matching_configs):
  • verification_status      • specialization_match
  • qualification_match      • experience_years
  • date_availability        • time_availability
  • location_distance        • preferred_radius_km
  • job_type_preference      • professional_status

Output per match:
  match_score: 0–100
  score_components: [{factor, points, max_points}]
  reasons: ["Specialization match", "Experience match", ...]
```

Score components are stored/returned so the UI can explain why a doctor/job matched.

### 7.6 Privacy Enforcement Rules

| Rule | Implementation |
|------|----------------|
| Phone & personal email never public | Excluded from all public serializers; only returned to the owner |
| Career visibility | `VERIFIED_HOSPITALS` / `SELECTED_HOSPITALS` / `HIDDEN` — enforced at query level |
| Detailed availability | Only visible to verified healthcare institutions |
| Profile visibility | `EVERYONE` / `DOCTORS_ONLY` / `CONNECTIONS_ONLY` — enforced at query level |
| Application snapshot | `JobApplication.metadata` stores the exact profile/document snapshot shared with the hospital at apply time |
| Credential documents | Private S3 objects; access only via expiring signed URLs; never public |
| Minimum compensation | Never returned in any public or hospital-facing API response |

### 7.7 Security & Infrastructure Checklist

| Item | Status | Notes |
|------|--------|-------|
| JWT access + refresh lifecycle | ✅ | `RefreshSession` model; revocation via `revoked_at` |
| Secure token rotation | ✅ | New refresh token issued on each refresh |
| RBAC + object-level authorization | ✅ | `user_type` check + hospital/doctor ownership checks per endpoint |
| Rate limiting | ✅ | `slowapi` on auth, search, messaging, reports |
| Encrypted transport | ✅ | HTTPS enforced via nginx + `HTTPSRedirectMiddleware` |
| Secure secret storage | ✅ | All secrets via `.env` / AWS Secrets Manager in production |
| Private object storage | ✅ | AWS S3 private bucket for credentials/documents |
| Signed/expiring document URLs | ✅ | `GET /api/v1/files/{id}/signed-url/` |
| File virus/type validation | ✅ | MIME type + size check on upload; `UPLOAD_INVALID` (400) on failure |
| Audit logs for sensitive actions | ✅ | `AuditLog` model; written on every verification/restriction/removal action |
| Database backups | ✅ | Configured via AWS RDS automated backups in production |
| Monitoring & structured logs | ✅ | Sentry DSN + structured logging middleware |

### 7.8 API Contract Standard

Every endpoint must document:

| Field | Description |
|-------|-------------|
| Method + Path | HTTP verb and URL pattern |
| Auth Role | Required `user_type` or `ANONYMOUS` |
| Request Schema | Pydantic model with field-level validation rules |
| Field Validation | min/max length, regex, required vs optional |
| Response Schema | Pydantic model for success response |
| Error Codes | All possible `error.code` values from the standard error table |
| Pagination | `page` + `page_size` query params; `meta.total` + `meta.has_next` in response |
| Idempotency | Whether the endpoint is idempotent; payment webhooks require idempotency key |
| Permission Checks | Object-level checks beyond role (e.g. hospital ownership, connection status) |
| Side Effects | DB writes, notifications triggered, audit log entries written |
| Notification Event | Which `NotificationEvent` code is fired (see Section 5.4) |
| Audit Event | Which `AuditLog.action` string is written |

**Standard response envelope:**
```json
// Success (single)
{"success": true, "data": {...}, "message": "..."}

// Success (list)
{"success": true, "data": [...], "meta": {"page": 1, "page_size": 20, "total": 125, "has_next": true}}

// Error
{"success": false, "error": {"code": "ERR_CODE", "message": "Human-readable", "fields": {"field": "reason"}}}
```

### 7.9 New Models Added (Spec 02)

The following models were added to complete the Spec 02 entity list:

| Model | App | Table | Purpose |
|-------|-----|-------|---------|
| `DoctorAffiliation` | `doctors` | `doctor_affiliations` | Current/past hospital affiliations with role, dates |
| `Follow` | `doctors` | `follows` | Doctor-to-doctor or doctor-to-hospital follow relationship |
| `Block` | `doctors` | `blocks` | User-level block; hides from feed/search, disables messaging |
| `JobSave` | `jobs` | `job_saves` | Doctor saves a job for later (replaces metadata JSONB approach) |
| `ShiftStatusHistory` | `shifts` | `shift_status_history` | Immutable audit trail for every shift request state transition |
| `DeviceToken` | `notifications` | `device_tokens` | FCM/APNs push tokens per device per user |
| `NotificationPreference` | `notifications` | `notification_preferences` | Per-user, per-event push + in-app channel preferences |
| `Plan` | `core` | `plans` | Billing plan definitions (name, price, cycle, features, limits) |
| `Subscription` | `core` | `subscriptions` | Hospital subscription to a plan with lifecycle status |
| `Entitlement` | `core` | `entitlements` | Active feature entitlements derived from a subscription |
| `Invoice` | `core` | `invoices` | Billing invoices linked to subscriptions |
| `Payment` | `core` | `payments` | Individual payment records with provider IDs and refund tracking |

**Migrations created:**
- `doctors/0011_add_affiliation_follow_block.py`
- `jobs/0003_add_job_save.py`
- `shifts/0002_add_shift_status_history.py`
- `notifications/0002_add_device_token_notification_preference.py`
- `core/0004_add_billing_models.py`

---

## 8. API Global Contract

### 8.1 Standard Response Envelopes

```json
// Success (single object)
{"success": true, "data": {...}, "message": "..."}

// Success (list)
{"success": true, "data": [...], "meta": {"page": 1, "page_size": 20, "total": 125, "has_next": true}}

// Error
{"success": false, "error": {"code": "ERR_CODE", "message": "Human-readable message", "fields": {"field": "reason"}}}
```

### 8.2 Standard Error Codes

| Code | Meaning | HTTP |
|------|---------|------|
| `AUTH_REQUIRED` | Access token missing/invalid | 401 |
| `AUTH_FORBIDDEN` | Role/object permission denied | 403 |
| `TOKEN_EXPIRED` | Access token expired | 401 |
| `SESSION_REVOKED` | Refresh/session revoked | 401 |
| `VALIDATION_ERROR` | Request field validation failed | 400 |
| `OTP_INVALID` | OTP invalid/expired | 400 |
| `RESOURCE_NOT_FOUND` | Resource does not exist or is not visible | 404 |
| `DUPLICATE_RESOURCE` | Unique relationship/resource already exists | 409 |
| `INVALID_STATE_TRANSITION` | Requested state change not allowed | 409 |
| `VERIFICATION_REQUIRED` | Action requires verified account | 403 |
| `PRIVACY_RESTRICTED` | Resource/field not visible to requester | 403/404 |
| `BLOCKED_RELATIONSHIP` | Blocked user relationship prevents action | 403 |
| `SHIFT_CONFLICT` | Accepted/confirmed shift overlaps existing commitment | 409 |
| `APPLICATION_CLOSED` | Job no longer accepts applications | 409 |
| `UPLOAD_INVALID` | File type/size/security validation failed | 400 |
| `FILE_ACCESS_DENIED` | Private file access denied | 403 |
| `RATE_LIMITED` | Too many requests | 429 |
| `IDEMPOTENCY_CONFLICT` | Same key used for incompatible request | 409 |
| `MODERATION_REQUIRED` | Content held for moderation | 202 |
| `SERVER_ERROR` | Unexpected server error | 500 |

### 8.3 Privacy Matrix

| Data | Public/Everyone | Doctors Only | Connections Only | Verified Hospitals |
|------|----------------|--------------|-----------------|-------------------|
| Name / photo / headline | Per profile visibility | Per setting | Per setting | Per setting |
| Phone / personal email | Never public | Controlled | Controlled | Controlled; not public |
| Medical registration details | Not exposed by default | Privacy-controlled | Privacy-controlled | Permitted professional fields only |
| Career opportunity status | Only if career visibility permits | If permitted | If permitted | Primary audience |
| Detailed availability | Not public | Generally restricted | Generally restricted | Primarily verified institutions |
| Min compensation | Never public | Never public | Never public | Private to doctor |
| Credential documents | Never public | Never public | Never public | Authorized access via signed URL only |

---

## 9. System Architecture

### 9.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐     ┌─────────────────────┐                        │
│  │  Doctor Mobile App  │     │  Hospital CRM       │                        │
│  │  (Android Native)   │     │  (React Web)        │                        │
│  └──────────┬──────────┘     └──────────┬──────────┘                        │
│             │                            │                                  │
│             └──────────┬─────────────────┘                                  │
│                        │                                                    │
└────────────────────────┼────────────────────────────────────────────────────┘
                         │ HTTPS / REST API
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY / NGINX                                 │
│                         (Load Balancer + SSL Termination)                   │
└─────────────────────────────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                        FastAPI Layer                             │       │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │       │
│  │  │ Auth     │ │ Doctors  │ │ Network  │ │  Jobs    │             │       │
│  │  │ Router   │ │ Router   │ │ Router   │ │ Router   │             │       │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │       │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │       │
│  │  │ Avail-   │ │ Messages │ │ Notific- │ │ Admin    │             │       │
│  │  │ ability  │ │ Router   │ │ ations   │ │ Router   │             │       │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                                    │                                        │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                      Django 5.0+ Core Layer                      │       │
│  │                                                                  │       │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐             │       │
│  │  │ Models   │ │ Admin    │ │ ORM      │ │ Celery   │             │       │
│  │  │ Layer    │ │ Interface│ │ Queries  │ │ Tasks    │             │       │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘             │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DATA & CACHE LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────┐      │
│  │   PostgreSQL    │    │    Redis        │    │   Celery + Redis    │      │
│  │   16+           │    │   7.2+          │    │   (Background Tasks)│      │
│  └─────────────────┘    └─────────────────┘    └─────────────────────┘      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                     AWS S3 (File Storage)                       │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW DIAGRAM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DOCTOR REGISTRATION FLOW:                                                  │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐    │
│  │ Mobile  │──▶│ OTP     │──▶│ Profile  │──▶│ NMC      │──▶│ Verified  │  │
│  │ Number  │   │ Verify  │   │ Create   │   │ Verify   │   │ Profile   │    │
│  └─────────┘   └─────────┘   └──────────┘   └──────────┘   └───────────┘    │
│                                                                             │
│  JOB APPLICATION FLOW:                                                      │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐    │
│  │ Browse  │──▶│ Apply   │──▶│ Shortlist│──▶│ Interview│──▶│ Hired/    │  │
│  │ Jobs    │   │ One-Tap │   │          │   │          │   │ Rejected  │    │
│  └─────────┘   └─────────┘   └──────────┘   └──────────┘   └───────────┘    │
│                                                                             │
│  SHIFT REQUEST FLOW:                                                        │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐    │
│  │ Create  │──▶│ Match   │──▶│ Send     │──▶│ Accept/  │──▶│ Confirm/  │  │
│  │ Request │   │ Doctors │   │ Request  │   │ Decline  │   │ Complete  │    │
│  └─────────┘   └─────────┘   └──────────┘   └──────────┘   └───────────┘    │
│                                                                             │
│  HOSPITAL REGISTRATION FLOW:                                                │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐    │
│  │ Admin   │──▶│ OTP     │──▶│ Hospital │──▶│ Document │──▶│ Verified  │  │
│  │ Phone   │   │ Verify  │   │ Details  │   │ Upload   │   │ Hospital  │    │
│  └─────────┘   └─────────┘   └──────────┘   └──────────┘   └───────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Technology Stack

### 10.1 Core Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Backend Core** | Django | 5.0.6 | ORM, Admin, Models, Auth |
| **API Layer** | FastAPI | 0.115+ | High-performance REST API |
| **Database** | PostgreSQL | 16+ | Primary database with advanced features |
| **Cache/Broker** | Redis | 7.2+ | Caching and Celery broker |
| **Task Queue** | Celery | 5.4+ | Background task processing |
| **API Docs** | FastAPI Swagger | - | Automatic OpenAPI documentation |
| **Validation** | Pydantic | 2.13+ | Data validation and serialization |
| **Auth** | SimpleJWT | 5.3+ | JWT access + refresh tokens |
| **WSGI Bridge** | a2wsgi | 1.10+ | Mount Django under FastAPI |

### 10.2 Frontend Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Mobile App** | Android Native | - | Doctor mobile application |
| **CRM Web** | React | 18+ | Hospital administration interface |
| **State Management** | Zustand/Redux | - | Client state management |
| **API Client** | React Query | - | Data fetching and caching |

### 10.3 DevOps & Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Containerization** | Docker | Container runtime |
| **Orchestration** | Docker Compose | Local development |
| **Hosting** | AWS EC2 / ECS | Production hosting |
| **CI/CD** | GitHub Actions | Automated deployment |
| **Monitoring** | Sentry / Prometheus | Error tracking |
| **Logging** | ELK Stack | Log aggregation |

### 10.4 PostgreSQL Extensions

```sql
-- Required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- Trigram similarity for fuzzy search
CREATE EXTENSION IF NOT EXISTS pgcrypto;     -- Cryptographic functions
CREATE EXTENSION IF NOT EXISTS uuid-ossp;    -- UUID generation
CREATE EXTENSION IF NOT EXISTS postgis;      -- Geospatial queries
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch; -- Fuzzy string matching
CREATE EXTENSION IF NOT EXISTS unaccent;     -- Unaccent text
```

---

## 11. Database Design

### 11.1 Complete Database Schema

> The schema below reflects the actual Django models. Additional fields `photo_base64`, `cover_base64` (DoctorProfile) and `logo_base64` (Hospital) are stored as base64 text for dev convenience alongside S3 file IDs.

```sql
-- ============================================================
-- CORE TABLES
-- ============================================================

-- 1. Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('DOCTOR', 'HOSPITAL_ADMIN', 'HOSPITAL_HR', 'ADMIN')),
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'DELETED')),
    is_super_admin BOOLEAN DEFAULT FALSE,  -- explicit Super Admin flag (separate from is_superuser)
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    search_vector TSVECTOR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. OTP Challenges Table
CREATE TABLE otp_challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(15) NOT NULL,
    purpose VARCHAR(20) NOT NULL CHECK (purpose IN ('LOGIN', 'REGISTER', 'RESET_PASSWORD')),
    otp_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 5,
    resend_count INTEGER DEFAULT 0,
    consumed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Refresh Sessions Table
CREATE TABLE refresh_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    device_id VARCHAR(255),
    device_name VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- DOCTOR MODULE TABLES
-- ============================================================

-- 4. Doctor Profiles
CREATE TABLE doctor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    photo_file_id UUID,
    headline VARCHAR(160),
    about TEXT,
    primary_specialization_id UUID,
    clinical_interests UUID[] DEFAULT '{}',
    professional_location JSONB,
    experience_years DECIMAL(4,1) DEFAULT 0,
    open_to_opportunities BOOLEAN DEFAULT FALSE,
    verification_status VARCHAR(20) DEFAULT 'UNVERIFIED' 
        CHECK (verification_status IN ('UNVERIFIED', 'PENDING', 'VERIFIED', 'REJECTED')),
    verification_rejected_reason TEXT,
    profile_visibility VARCHAR(20) DEFAULT 'EVERYONE'
        CHECK (profile_visibility IN ('EVERYONE', 'DOCTORS_ONLY', 'CONNECTIONS_ONLY')),
    career_visibility VARCHAR(20) DEFAULT 'VERIFIED_HOSPITALS'
        CHECK (career_visibility IN ('VERIFIED_HOSPITALS', 'SELECTED_HOSPITALS', 'HIDDEN')),
    search_vector TSVECTOR,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create GIN indexes for JSON fields
CREATE INDEX idx_doctor_location_gin ON doctor_profiles USING GIN (professional_location);
CREATE INDEX idx_doctor_metadata_gin ON doctor_profiles USING GIN (metadata);
CREATE INDEX idx_doctor_search_gin ON doctor_profiles USING GIN (search_vector);

-- 5. Doctor Registrations
CREATE TABLE doctor_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id UUID NOT NULL REFERENCES doctor_profiles(id) ON DELETE CASCADE,
    council_id UUID NOT NULL,
    registration_number VARCHAR(50) NOT NULL,
    registration_year INTEGER NOT NULL,
    is_primary BOOLEAN DEFAULT TRUE,
    verification_status VARCHAR(20) DEFAULT 'PENDING'
        CHECK (verification_status IN ('PENDING', 'VERIFIED', 'REJECTED')),
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(council_id, registration_number)
);

-- 6. Doctor Qualifications
CREATE TABLE doctor_qualifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id UUID NOT NULL REFERENCES doctor_profiles(id) ON DELETE CASCADE,
    degree VARCHAR(100) NOT NULL,
    institution VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL,
    specialization VARCHAR(100),
    file_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Doctor Experiences
CREATE TABLE doctor_experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id UUID NOT NULL REFERENCES doctor_profiles(id) ON DELETE CASCADE,
    role VARCHAR(100) NOT NULL,
    hospital_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    start_date DATE NOT NULL,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- HOSPITAL MODULE TABLES
-- ============================================================

-- 8. Hospitals
CREATE TABLE hospitals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('HOSPITAL', 'CLINIC', 'NURSING_HOME', 'MEDICAL_COLLEGE')),
    logo_file_id UUID,
    about TEXT,
    location JSONB NOT NULL,
    bed_count INTEGER,
    phone VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(255),
    verification_status VARCHAR(20) DEFAULT 'UNVERIFIED'
        CHECK (verification_status IN ('UNVERIFIED', 'PENDING', 'VERIFIED', 'REJECTED')),
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. Hospital Branches
CREATE TABLE hospital_branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_id UUID NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    location JSONB NOT NULL,
    phone VARCHAR(20),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. Hospital Departments
CREATE TABLE hospital_departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_id UUID NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES hospital_branches(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 11. Hospital Users
CREATE TABLE hospital_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hospital_id UUID NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES hospital_branches(id) ON DELETE SET NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('ADMIN', 'HR', 'RECRUITER')),
    designation VARCHAR(100),
    department_id UUID REFERENCES hospital_departments(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' 
        CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- JOBS & APPLICATIONS TABLES
-- ============================================================

-- 12. Job Posts
CREATE TABLE job_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_id UUID NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES hospital_branches(id) ON DELETE SET NULL,
    department_id UUID REFERENCES hospital_departments(id) ON DELETE SET NULL,
    title VARCHAR(160) NOT NULL,
    specialty_id UUID NOT NULL,
    qualification_ids UUID[] NOT NULL,
    description TEXT NOT NULL,
    responsibilities TEXT,
    requirements TEXT,
    location JSONB NOT NULL,
    salary_min DECIMAL(12,2),
    salary_max DECIMAL(12,2),
    salary_visibility VARCHAR(20) DEFAULT 'PUBLIC'
        CHECK (salary_visibility IN ('PUBLIC', 'ON_REQUEST', 'HIDDEN')),
    currency VARCHAR(3) DEFAULT 'INR',
    job_type VARCHAR(20) NOT NULL 
        CHECK (job_type IN ('FULL_TIME', 'PART_TIME', 'VISITING', 'LOCUM', 'CONTRACT')),
    experience_min_years DECIMAL(4,1) DEFAULT 0,
    experience_max_years DECIMAL(4,1),
    shift_type VARCHAR(20) DEFAULT 'DAY' 
        CHECK (shift_type IN ('DAY', 'NIGHT', 'ROTATIONAL', 'FLEXIBLE')),
    joining_requirement VARCHAR(50),
    positions INTEGER DEFAULT 1,
    is_urgent BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'DRAFT' 
        CHECK (status IN ('DRAFT', 'PUBLISHED', 'CLOSED', 'EXPIRED', 'FILLED')),
    posted_by UUID NOT NULL REFERENCES users(id),
    published_at TIMESTAMP WITH TIME ZONE,
    closing_date TIMESTAMP WITH TIME ZONE,
    search_vector TSVECTOR,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 13. Job Applications
CREATE TABLE job_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES job_posts(id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES doctor_profiles(id) ON DELETE CASCADE,
    cv_file_id UUID,
    status VARCHAR(20) DEFAULT 'APPLIED' 
        CHECK (status IN ('APPLIED', 'PROFILE_VIEWED', 'SHORTLISTED', 
                         'INTERVIEW', 'OFFERED', 'HIRED', 'REJECTED', 'WITHDRAWN')),
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_id, doctor_id)
);

-- 14. Application History
CREATE TABLE application_histories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES job_applications(id) ON DELETE CASCADE,
    from_status VARCHAR(20),
    to_status VARCHAR(20) NOT NULL,
    changed_by UUID NOT NULL REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- AVAILABILITY EXCHANGE TABLES
-- ============================================================

-- 15. Doctor Availability
CREATE TABLE doctor_availabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id UUID NOT NULL REFERENCES doctor_profiles(id) ON DELETE CASCADE,
    availability_type VARCHAR(20) NOT NULL 
        CHECK (availability_type IN ('LOCUM', 'VISITING', 'TEMPORARY', 'PART_TIME')),
    available_from DATE NOT NULL,
    available_until DATE NOT NULL,
    preferred_location JSONB,
    preferred_radius_km INTEGER,
    minimum_compensation DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'INR',
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 16. Availability Slots
CREATE TABLE availability_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    availability_id UUID NOT NULL REFERENCES doctor_availabilities(id) ON DELETE CASCADE,
    slot_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_booked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CHECK (start_time < end_time)
);

-- 17. Shift Requirements
CREATE TABLE shift_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_id UUID NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES hospital_branches(id) ON DELETE SET NULL,
    specialty_id UUID NOT NULL,
    qualification_ids UUID[] NOT NULL,
    requirement_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    location JSONB NOT NULL,
    compensation DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    doctors_required INTEGER DEFAULT 1,
    urgency VARCHAR(20) DEFAULT 'NORMAL' 
        CHECK (urgency IN ('NORMAL', 'URGENT', 'IMMEDIATE')),
    notes TEXT,
    status VARCHAR(20) DEFAULT 'OPEN' 
        CHECK (status IN ('OPEN', 'FILLED', 'CANCELLED', 'EXPIRED')),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 18. Shift Requests
CREATE TABLE shift_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_id UUID NOT NULL REFERENCES shift_requirements(id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES doctor_profiles(id) ON DELETE CASCADE,
    status VARCHAR(30) DEFAULT 'REQUESTED' 
        CHECK (status IN ('REQUESTED', 'ACCEPTED_BY_DOCTOR', 'DECLINED_BY_DOCTOR',
                         'CONFIRMED_BY_HOSPITAL', 'COMPLETED', 'CANCELLED')),
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE,
    declined_at TIMESTAMP WITH TIME ZONE,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    UNIQUE(requirement_id, doctor_id)
);

-- ============================================================
-- MESSAGING & NOTIFICATIONS TABLES
-- ============================================================

-- 19. Conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL CHECK (type IN ('DIRECT', 'GROUP')),
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 20. Conversation Participants
CREATE TABLE conversation_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    last_read_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(conversation_id, user_id)
);

-- 21. Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT,
    file_id UUID,
    file_type VARCHAR(50),
    file_name VARCHAR(255),
    file_size INTEGER,
    message_type VARCHAR(20) DEFAULT 'TEXT'
        CHECK (message_type IN ('TEXT', 'IMAGE', 'DOCUMENT', 'SHIFT_REQUEST', 'JOB_REFERRAL')),
    metadata JSONB,
    read_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 22. Notifications
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    data_json JSONB,
    deep_link VARCHAR(255),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

-- GiST index for geospatial queries
CREATE INDEX idx_hospital_location_gist ON hospitals USING GIST (location);
CREATE INDEX idx_doctor_location_gist ON doctor_profiles USING GIST (professional_location);

-- Full-text search indexes
CREATE INDEX idx_users_search_gin ON users USING GIN (search_vector);
CREATE INDEX idx_job_search_gin ON job_posts USING GIN (search_vector);

-- Array field indexes
CREATE INDEX idx_job_qualifications_gin ON job_posts USING GIN (qualification_ids);
CREATE INDEX idx_doctor_interests_gin ON doctor_profiles USING GIN (clinical_interests);

-- Composite indexes for common queries
CREATE INDEX idx_job_hospital_status ON job_posts(hospital_id, status);
CREATE INDEX idx_job_specialty_status ON job_posts(specialty_id, status);
CREATE INDEX idx_application_job_status ON job_applications(job_id, status);
CREATE INDEX idx_shift_requirement_status ON shift_requirements(hospital_id, status);

-- ============================================================
-- TRIGGERS FOR SEARCH VECTORS
-- ============================================================

-- Auto-update search vectors
CREATE OR REPLACE FUNCTION update_user_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector = 
        setweight(to_tsvector('english', COALESCE(NEW.phone, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.email, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_search_vector_update
    BEFORE INSERT OR UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_user_search_vector();
```

---

## 12. API Architecture (FastAPI)

### 12.1 FastAPI Integration with Django

FastAPI is mounted alongside Django using `a2wsgi`. Django handles ORM, Admin and models; FastAPI handles all REST API endpoints. See `fastapi_app/main.py` for the full implementation.

**Entry point:** `run.py` starts uvicorn serving the combined app on port 8000.

---

## 13. Project Structure
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import asyncio
from typing import Optional

# Django setup
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docconnect_backend.settings')
django.setup()

# Import Django models
from django.contrib.auth import get_user_model
from doctors.models import DoctorProfile
from jobs.models import JobPost

# FastAPI app
app = FastAPI(
    title="DocConnect API",
    description="Verified Professional Network for Doctors",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# ============================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current authenticated user from JWT token"""
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    
    token = credentials.credentials
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        User = get_user_model()
        user = User.objects.get(id=user_id)
        if user.status != 'ACTIVE':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active"
            )
        return user
    except (InvalidToken, TokenError, User.DoesNotExist):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_doctor(
    current_user = Depends(get_current_user)
):
    """Get current authenticated doctor"""
    if current_user.user_type != 'DOCTOR':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a doctor"
        )
    try:
        return current_user.doctor_profile
    except DoctorProfile.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum

class UserType(str, Enum):
    DOCTOR = "DOCTOR"
    HOSPITAL_ADMIN = "HOSPITAL_ADMIN"
    HOSPITAL_HR = "HOSPITAL_HR"
    ADMIN = "ADMIN"

class VerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

# Auth Schemas
class OTPRequest(BaseModel):
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    purpose: str = Field(..., pattern=r'^(LOGIN|REGISTER|RESET_PASSWORD)$')

class OTPVerify(BaseModel):
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    otp: str = Field(..., min_length=6, max_length=6)
    device_id: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Doctor Schemas
class Location(BaseModel):
    address: Optional[str] = None
    city: str
    state: str
    pincode: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None

class DoctorRegistration(BaseModel):
    council_id: str
    registration_number: str
    registration_year: int

class DoctorQualification(BaseModel):
    degree: str
    institution: str
    year: int
    specialization: Optional[str] = None

class DoctorExperience(BaseModel):
    role: str
    hospital_name: str
    location: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None

class DoctorProfileCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str = Field(..., min_length=1, max_length=80)
    headline: Optional[str] = Field(None, max_length=160)
    about: Optional[str] = None
    primary_specialization_id: Optional[str] = None
    clinical_interests: Optional[List[str]] = []
    professional_location: Optional[Location] = None
    experience_years: Optional[float] = Field(0, ge=0, le=60)

class DoctorProfileResponse(BaseModel):
    id: str
    user_id: str
    first_name: str
    last_name: str
    full_name: str
    photo_file_id: Optional[str]
    headline: Optional[str]
    about: Optional[str]
    primary_specialization_id: Optional[str]
    clinical_interests: List[str]
    professional_location: Optional[Location]
    experience_years: float
    open_to_opportunities: bool
    verification_status: VerificationStatus
    is_verified: bool
    created_at: datetime
    updated_at: datetime

# Job Schemas
class JobType(str, Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    VISITING = "VISITING"
    LOCUM = "LOCUM"
    CONTRACT = "CONTRACT"

class SalaryVisibility(str, Enum):
    PUBLIC = "PUBLIC"
    ON_REQUEST = "ON_REQUEST"
    HIDDEN = "HIDDEN"

class JobCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=160)
    specialty_id: str
    qualification_ids: List[str]
    description: str
    responsibilities: Optional[str] = None
    requirements: Optional[str] = None
    location: Location
    salary_min: Optional[Decimal] = Field(None, ge=0)
    salary_max: Optional[Decimal] = Field(None, ge=0)
    salary_visibility: SalaryVisibility = SalaryVisibility.PUBLIC
    currency: str = "INR"
    job_type: JobType
    experience_min_years: float = 0
    experience_max_years: Optional[float] = None
    shift_type: str = "DAY"
    joining_requirement: Optional[str] = None
    positions: int = Field(1, ge=1)
    is_urgent: bool = False

class JobResponse(BaseModel):
    id: str
    hospital_id: str
    hospital_name: str
    title: str
    specialty_id: str
    description: str
    location: Location
    salary_min: Optional[Decimal]
    salary_max: Optional[Decimal]
    salary_visibility: SalaryVisibility
    job_type: JobType
    experience_min_years: float
    experience_max_years: Optional[float]
    is_urgent: bool
    status: str
    created_at: datetime
    published_at: Optional[datetime]
    match_score: Optional[int] = None

# Availability Schemas
class AvailabilityType(str, Enum):
    LOCUM = "LOCUM"
    VISITING = "VISITING"
    TEMPORARY = "TEMPORARY"
    PART_TIME = "PART_TIME"

class AvailabilitySlot(BaseModel):
    slot_date: date
    start_time: time
    end_time: time

class AvailabilityCreate(BaseModel):
    availability_type: AvailabilityType
    available_from: date
    available_until: date
    preferred_location: Optional[Location] = None
    preferred_radius_km: Optional[int] = Field(None, ge=1, le=500)
    minimum_compensation: Optional[Decimal] = Field(None, ge=0)
    currency: str = "INR"
    notes: Optional[str] = None
    slots: List[AvailabilitySlot]

class ShiftRequirementCreate(BaseModel):
    specialty_id: str
    qualification_ids: List[str]
    requirement_date: date
    start_time: time
    end_time: time
    location: Location
    compensation: Decimal = Field(..., ge=0)
    currency: str = "INR"
    doctors_required: int = Field(1, ge=1)
    urgency: str = "NORMAL"
    notes: Optional[str] = None

# Hospital Schemas
class HospitalType(str, Enum):
    HOSPITAL = "HOSPITAL"
    CLINIC = "CLINIC"
    NURSING_HOME = "NURSING_HOME"
    MEDICAL_COLLEGE = "MEDICAL_COLLEGE"

class HospitalAdminRole(str, Enum):
    ADMIN = "ADMIN"
    HR = "HR"
    RECRUITER = "RECRUITER"

class HospitalRegisterRequest(BaseModel):
    # Admin user details
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    email: EmailStr
    # Hospital details
    name: str = Field(..., min_length=3, max_length=255)
    type: HospitalType
    about: Optional[str] = None
    location: Location
    bed_count: Optional[int] = Field(None, ge=1)
    hospital_phone: Optional[str] = None
    hospital_email: Optional[EmailStr] = None
    website: Optional[str] = None

class HospitalResponse(BaseModel):
    id: str
    name: str
    type: HospitalType
    about: Optional[str]
    location: Location
    bed_count: Optional[int]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    verification_status: VerificationStatus
    created_at: datetime

class HospitalBranchCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    location: Location
    phone: Optional[str] = None
    is_primary: bool = False

class HospitalDepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    branch_id: Optional[str] = None

class HospitalUserInvite(BaseModel):
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    email: EmailStr
    role: HospitalAdminRole
    designation: Optional[str] = None
    branch_id: Optional[str] = None
    department_id: Optional[str] = None

# ============================================================
# FASTAPI ROUTERS
# ============================================================

from fastapi import APIRouter, Query, Body, File, UploadFile
from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

# Auth Router
auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@auth_router.post("/send-otp/", response_model=Dict[str, Any])
async def send_otp(request: OTPRequest):
    """Send OTP to user's phone number"""
    from accounts.models import OTPChallenge
    from core.services.sms import send_otp_sms
    import secrets
    import hashlib
    from datetime import timedelta
    from django.utils import timezone
    
    # Generate OTP
    otp = str(secrets.randbelow(900000) + 100000)
    otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    expires_at = timezone.now() + timedelta(seconds=300)
    
    # Store OTP
    OTPChallenge.objects.create(
        phone=request.phone,
        purpose=request.purpose,
        otp_hash=otp_hash,
        expires_at=expires_at
    )
    
    # Send OTP
    await send_otp_sms(request.phone, otp)
    
    return {
        "success": True,
        "message": "OTP sent successfully",
        "expires_in": 300
    }

@auth_router.post("/verify-otp/", response_model=TokenResponse)
async def verify_otp(request: OTPVerify):
    """Verify OTP and authenticate user"""
    from accounts.models import OTPChallenge, RefreshSession
    from rest_framework_simplejwt.tokens import RefreshToken
    from django.contrib.auth import get_user_model
    import hashlib
    from django.utils import timezone
    
    User = get_user_model()
    
    # Find OTP
    challenges = OTPChallenge.objects.filter(
        phone=request.phone,
        purpose='LOGIN',
        consumed_at__isnull=True,
        expires_at__gt=timezone.now()
    ).order_by('-created_at')
    
    if not challenges.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid OTP found"
        )
    
    challenge = challenges.first()
    otp_hash = hashlib.sha256(request.otp.encode()).hexdigest()
    
    if challenge.otp_hash != otp_hash:
        challenge.attempts += 1
        challenge.save()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    # Mark as consumed
    challenge.consumed_at = timezone.now()
    challenge.save()
    
    # Get or create user
    user, created = User.objects.get_or_create(
        phone=request.phone,
        defaults={'user_type': 'DOCTOR'}
    )
    
    # Generate tokens
    refresh = RefreshToken.for_user(user)
    
    return TokenResponse(
        access_token=str(refresh.access_token),
        refresh_token=str(refresh)
    )

# Hospital Router
hospital_router = APIRouter(prefix="/api/v1/hospitals", tags=["Hospitals"])

@hospital_router.post("/register/", response_model=HospitalResponse, status_code=201)
async def register_hospital(
    data: HospitalRegisterRequest,
    current_user = Depends(get_current_user)
):
    """Register a new hospital and link admin user"""
    from hospitals.models import Hospital, HospitalUser

    if current_user.user_type not in ('HOSPITAL_ADMIN', 'ADMIN'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hospital admins can register a hospital"
        )

    if HospitalUser.objects.filter(user=current_user).exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already associated with a hospital"
        )

    hospital = Hospital.objects.create(
        name=data.name,
        type=data.type,
        about=data.about,
        location=data.location.dict(),
        bed_count=data.bed_count,
        phone=data.hospital_phone,
        email=str(data.hospital_email) if data.hospital_email else None,
        website=data.website,
        verification_status='PENDING'
    )

    HospitalUser.objects.create(
        user=current_user,
        hospital=hospital,
        role='ADMIN'
    )

    return HospitalResponse(
        id=str(hospital.id),
        name=hospital.name,
        type=hospital.type,
        about=hospital.about,
        location=data.location,
        bed_count=hospital.bed_count,
        phone=hospital.phone,
        email=hospital.email,
        website=hospital.website,
        verification_status=hospital.verification_status,
        created_at=hospital.created_at
    )

@hospital_router.get("/me/", response_model=HospitalResponse)
async def get_my_hospital(
    current_user = Depends(get_current_user)
):
    """Get hospital profile of the logged-in admin"""
    from hospitals.models import HospitalUser

    try:
        hospital_user = HospitalUser.objects.select_related('hospital').get(user=current_user)
        h = hospital_user.hospital
        return HospitalResponse(
            id=str(h.id),
            name=h.name,
            type=h.type,
            about=h.about,
            location=h.location,
            bed_count=h.bed_count,
            phone=h.phone,
            email=h.email,
            website=h.website,
            verification_status=h.verification_status,
            created_at=h.created_at
        )
    except HospitalUser.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hospital associated with this user"
        )

@hospital_router.post("/me/branches/", status_code=201)
async def add_branch(
    branch: HospitalBranchCreate,
    current_user = Depends(get_current_user)
):
    """Add a branch to the hospital"""
    from hospitals.models import HospitalUser, HospitalBranch

    try:
        hospital_user = HospitalUser.objects.get(user=current_user, role='ADMIN')
    except HospitalUser.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a hospital admin")

    b = HospitalBranch.objects.create(
        hospital=hospital_user.hospital,
        name=branch.name,
        location=branch.location.dict(),
        phone=branch.phone,
        is_primary=branch.is_primary
    )
    return {"success": True, "branch_id": str(b.id), "name": b.name}

@hospital_router.post("/me/departments/", status_code=201)
async def add_department(
    dept: HospitalDepartmentCreate,
    current_user = Depends(get_current_user)
):
    """Add a department to the hospital"""
    from hospitals.models import HospitalUser, HospitalDepartment

    try:
        hospital_user = HospitalUser.objects.get(user=current_user, role='ADMIN')
    except HospitalUser.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a hospital admin")

    d = HospitalDepartment.objects.create(
        hospital=hospital_user.hospital,
        branch_id=dept.branch_id,
        name=dept.name
    )
    return {"success": True, "department_id": str(d.id), "name": d.name}

@hospital_router.post("/me/invite-user/", status_code=201)
async def invite_hospital_user(
    invite: HospitalUserInvite,
    current_user = Depends(get_current_user)
):
    """Invite HR/Recruiter to the hospital account"""
    from hospitals.models import HospitalUser
    from django.contrib.auth import get_user_model

    try:
        hospital_user = HospitalUser.objects.get(user=current_user, role='ADMIN')
    except HospitalUser.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a hospital admin")

    User = get_user_model()
    invited_user, _ = User.objects.get_or_create(
        phone=invite.phone,
        defaults={'email': str(invite.email), 'user_type': 'HOSPITAL_HR'}
    )

    if HospitalUser.objects.filter(user=invited_user).exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already associated with a hospital"
        )

    HospitalUser.objects.create(
        user=invited_user,
        hospital=hospital_user.hospital,
        role=invite.role,
        designation=invite.designation,
        branch_id=invite.branch_id,
        department_id=invite.department_id
    )
    return {"success": True, "message": f"User {invite.phone} added as {invite.role}"}

@hospital_router.post("/me/upload-logo/")
async def upload_hospital_logo(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Upload hospital logo to S3"""
    from hospitals.models import HospitalUser
    from core.services.storage import upload_file_to_s3

    try:
        hospital_user = HospitalUser.objects.get(user=current_user, role='ADMIN')
    except HospitalUser.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a hospital admin")

    if file.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only JPEG/PNG/WEBP allowed")

    file_id = await upload_file_to_s3(file, folder="hospital-logos")
    hospital_user.hospital.logo_file_id = file_id
    hospital_user.hospital.save(update_fields=['logo_file_id'])

    return {"success": True, "file_id": str(file_id)}

# Doctor Router
doctor_router = APIRouter(prefix="/api/v1/doctors", tags=["Doctors"])

@doctor_router.post("/profile/", response_model=DoctorProfileResponse)
async def create_doctor_profile(
    profile: DoctorProfileCreate,
    current_user = Depends(get_current_user)
):
    """Create doctor profile"""
    if current_user.user_type != 'DOCTOR':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a doctor"
        )
    
    doctor_profile = DoctorProfile.objects.create(
        user=current_user,
        first_name=profile.first_name,
        last_name=profile.last_name,
        headline=profile.headline,
        about=profile.about,
        primary_specialization_id=profile.primary_specialization_id,
        clinical_interests=profile.clinical_interests or [],
        professional_location=profile.professional_location.dict() if profile.professional_location else {},
        experience_years=profile.experience_years
    )
    
    return DoctorProfileResponse.from_orm(doctor_profile)

@doctor_router.get("/profile/me/", response_model=DoctorProfileResponse)
async def get_my_profile(
    current_doctor = Depends(get_current_doctor)
):
    """Get current doctor's profile"""
    return DoctorProfileResponse.from_orm(current_doctor)

@doctor_router.get("/search/")
async def search_doctors(
    search: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    experience_min: Optional[float] = Query(None),
    experience_max: Optional[float] = Query(None),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radius: Optional[int] = Query(50),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """Search doctors with advanced filters"""
    queryset = DoctorProfile.objects.filter(verification_status='VERIFIED')
    
    # Full-text search
    if search:
        vector = SearchVector('first_name', 'last_name', 'headline', 'about')
        query = SearchQuery(search)
        queryset = queryset.annotate(
            rank=SearchRank(vector, query)
        ).filter(rank__gte=0.1).order_by('-rank')
    
    # Filters
    if specialty:
        queryset = queryset.filter(primary_specialization_id=specialty)
    if city:
        queryset = queryset.filter(professional_location__city__icontains=city)
    if state:
        queryset = queryset.filter(professional_location__state__icontains=state)
    if experience_min:
        queryset = queryset.filter(experience_years__gte=experience_min)
    if experience_max:
        queryset = queryset.filter(experience_years__lte=experience_max)
    
    # Geospatial search
    if lat and lng:
        from django.contrib.gis.geos import Point
        from django.contrib.gis.db.models.functions import Distance
        point = Point(lng, lat, srid=4326)
        queryset = queryset.filter(
            professional_location__has_key='coordinates'
        ).annotate(
            distance=Distance('professional_location__coordinates', point)
        ).filter(distance__lte=radius * 1000)
    
    # Pagination
    offset = (page - 1) * page_size
    total = queryset.count()
    results = queryset[offset:offset + page_size]
    
    return {
        "results": [DoctorProfileResponse.from_orm(d) for d in results],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

# Job Router
job_router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

@job_router.post("/", response_model=JobResponse)
async def create_job(
    job: JobCreate,
    current_user = Depends(get_current_user)
):
    """Create a new job posting"""
    from hospitals.models import HospitalUser
    
    # Check if user is hospital staff
    try:
        hospital_user = HospitalUser.objects.get(user=current_user)
        hospital = hospital_user.hospital
    except HospitalUser.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a hospital"
        )
    
    # Create job
    job_post = JobPost.objects.create(
        hospital=hospital,
        title=job.title,
        specialty_id=job.specialty_id,
        qualification_ids=job.qualification_ids,
        description=job.description,
        responsibilities=job.responsibilities,
        requirements=job.requirements,
        location=job.location.dict(),
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_visibility=job.salary_visibility,
        currency=job.currency,
        job_type=job.job_type,
        experience_min_years=job.experience_min_years,
        experience_max_years=job.experience_max_years,
        shift_type=job.shift_type,
        joining_requirement=job.joining_requirement,
        positions=job.positions,
        is_urgent=job.is_urgent,
        status='PUBLISHED',
        posted_by=current_user,
        published_at=datetime.now()
    )
    
    return JobResponse.from_orm(job_post)

@job_router.get("/")
async def list_jobs(
    specialty: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """List jobs with filters"""
    queryset = JobPost.objects.filter(status='PUBLISHED')
    
    if specialty:
        queryset = queryset.filter(specialty_id=specialty)
    if city:
        queryset = queryset.filter(location__city__icontains=city)
    if job_type:
        queryset = queryset.filter(job_type=job_type)
    if search:
        vector = SearchVector('title', 'description')
        query = SearchQuery(search)
        queryset = queryset.annotate(
            rank=SearchRank(vector, query)
        ).filter(rank__gte=0.1).order_by('-rank')
    
    # Pagination
    offset = (page - 1) * page_size
    total = queryset.count()
    results = queryset[offset:offset + page_size]
    
    return {
        "results": [JobResponse.from_orm(j) for j in results],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@job_router.get("/{job_id}/", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user = Depends(get_current_user)
):
    """Get job details"""
    try:
        job = JobPost.objects.get(id=job_id, status='PUBLISHED')
        return JobResponse.from_orm(job)
    except JobPost.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

@job_router.post("/{job_id}/apply/")
async def apply_to_job(
    job_id: str,
    cv_file_id: Optional[str] = None,
    current_doctor = Depends(get_current_doctor)
):
    """Apply to a job"""
    from jobs.models import JobApplication
    
    try:
        job = JobPost.objects.get(id=job_id, status='PUBLISHED')
    except JobPost.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check if already applied
    if JobApplication.objects.filter(job=job, doctor=current_doctor).exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already applied to this job"
        )
    
    # Create application
    application = JobApplication.objects.create(
        job=job,
        doctor=current_doctor,
        cv_file_id=cv_file_id,
        status='APPLIED'
    )
    
    return {
        "success": True,
        "message": "Application submitted successfully",
        "application_id": str(application.id),
        "status": application.status
    }

# Availability Router
availability_router = APIRouter(prefix="/api/v1/availability", tags=["Availability"])

@availability_router.post("/")
async def create_availability(
    availability: AvailabilityCreate,
    current_doctor = Depends(get_current_doctor)
):
    """Create doctor availability"""
    from availability.models import DoctorAvailability, AvailabilitySlot
    
    # Create availability
    avail = DoctorAvailability.objects.create(
        doctor=current_doctor,
        availability_type=availability.availability_type,
        available_from=availability.available_from,
        available_until=availability.available_until,
        preferred_location=availability.preferred_location.dict() if availability.preferred_location else {},
        preferred_radius_km=availability.preferred_radius_km,
        minimum_compensation=availability.minimum_compensation,
        currency=availability.currency,
        notes=availability.notes,
        is_active=True
    )
    
    # Create slots
    for slot in availability.slots:
        AvailabilitySlot.objects.create(
            availability=avail,
            slot_date=slot.slot_date,
            start_time=slot.start_time,
            end_time=slot.end_time
        )
    
    return {
        "success": True,
        "message": "Availability created successfully",
        "availability_id": str(avail.id)
    }

# Shift Router
shift_router = APIRouter(prefix="/api/v1/shifts", tags=["Shifts"])

@shift_router.post("/requirements/")
async def create_shift_requirement(
    requirement: ShiftRequirementCreate,
    current_user = Depends(get_current_user)
):
    """Create a shift requirement"""
    from shifts.models import ShiftRequirement
    from hospitals.models import HospitalUser
    
    try:
        hospital_user = HospitalUser.objects.get(user=current_user)
        hospital = hospital_user.hospital
    except HospitalUser.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a hospital"
        )
    
    shift_req = ShiftRequirement.objects.create(
        hospital=hospital,
        specialty_id=requirement.specialty_id,
        qualification_ids=requirement.qualification_ids,
        requirement_date=requirement.requirement_date,
        start_time=requirement.start_time,
        end_time=requirement.end_time,
        location=requirement.location.dict(),
        compensation=requirement.compensation,
        currency=requirement.currency,
        doctors_required=requirement.doctors_required,
        urgency=requirement.urgency,
        notes=requirement.notes,
        created_by=current_user
    )
    
    return {
        "success": True,
        "message": "Shift requirement created successfully",
        "requirement_id": str(shift_req.id)
    }

# ============================================================
# REGISTER ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(hospital_router)
app.include_router(doctor_router)
app.include_router(job_router)
app.include_router(availability_router)


```
docconnect/
├── manage.py
├── run.py                     # FastAPI + Django combined runner
├── requirements.txt
├── .env
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── README.md
│
├── docconnect_backend/        # Django Project
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   ├── celery.py
│   ├── wsgi.py
│   └── asgi.py
│
├── fastapi_app/               # FastAPI Application
│   ├── __init__.py
│   ├── main.py                # Main FastAPI app + Django mount
│   ├── dependencies.py        # get_current_user / get_current_doctor
│   ├── schemas.py             # Shared Pydantic models
│   ├── routers/               # API routers
│   │   ├── __init__.py
│   │   ├── admin.py           # Admin CRM: verification, users, reports, moderation,
│   │   │                      # communities, audit logs, analytics, settings, matching config
│   │   ├── auth.py            # Register, Login, OTP, Refresh, Logout
│   │   ├── availability.py    # Doctor availability + slots
│   │   ├── billing.py         # Plans, subscriptions, invoices, webhooks, refunds
│   │   ├── communities.py     # Specialty communities
│   │   ├── devices.py         # Push notification device tokens
│   │   ├── doctors.py         # Profile, Search, Qualifications, Experience
│   │   ├── feed.py            # Home, Posts, Likes, Comments, Replies
│   │   ├── files.py           # File upload, signed URLs
│   │   ├── hospitals.py       # Register, Branches, Departments, Staff
│   │   ├── jobs.py            # Post, Apply, Withdraw, CRM pipeline
│   │   ├── masters.py         # Specialties, qualifications, councils, job/shift types
│   │   ├── messaging.py       # Conversations + Messages
│   │   ├── network.py         # Connections, follow, block, reports
│   │   ├── notifications.py   # List, Read, Unread count, preferences
│   │   ├── search.py          # Universal search
│   │   ├── shifts.py          # Requirements, Requests, Lifecycle
│   │   └── support.py         # Support tickets + admin ticket management
│   └── middleware/
│       ├── __init__.py
│       ├── auth.py
│       └── logging.py
│
├── apps/                      # Django Apps
│   ├── accounts/              # User, OTPChallenge, RefreshSession
│   ├── doctors/               # DoctorProfile, Connection, Post, PostLike, PostComment
│   ├── hospitals/             # Hospital, Branch, Department, HospitalUser, HospitalFollow
│   ├── jobs/                  # JobPost, JobApplication, ApplicationHistory
│   ├── availability/          # DoctorAvailability, AvailabilitySlot
│   ├── shifts/                # ShiftRequirement, ShiftRequest
│   ├── messaging/             # Conversation, ConversationParticipant, Message
│   ├── notifications/         # Notification
│   └── core/                  # Community, CommunityMember, AuditLog, Report,
│                              # SupportTicket, SupportMessage, MatchingConfig,
│                              # Specialization, Qualification, Council
│                              # + services: Encryption, SMS, S3 storage
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_doctors.py
│   ├── test_jobs.py
│   └── test_availability.py
│
├── scripts/
│   ├── seed_data.py
│   ├── create_admin.py
│   └── update_search_vectors.py
│
├── templates/                 # Django HTML templates (web UI)
├── nginx/
│   └── nginx.conf
└── docs/
```

---

## 14. Development Setup

### 14.1 Prerequisites

- Python 3.11+ (3.13 / 3.14 also tested on Windows)
- PostgreSQL 16+
- Redis 7.2+

### 14.2 Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/pkdubey/docconnect.git
cd docconnect

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env with your DB credentials

# 5. Setup PostgreSQL (run in psql as postgres user)
# CREATE DATABASE docconnect_db;
# CREATE USER docconnect_user WITH PASSWORD 'docconnect_password';
# GRANT ALL PRIVILEGES ON DATABASE docconnect_db TO docconnect_user;

# 6. Create migrations for all apps
python manage.py makemigrations accounts doctors hospitals jobs availability shifts messaging notifications
python manage.py makemigrations core

# 7. Run all migrations
python manage.py migrate

# 8. Seed master data (specializations, qualifications, councils)
python scripts/seed_data.py

# 9. Create superuser
python -c "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','docconnect_backend.settings.development'); django.setup(); from apps.accounts.models import User; User.objects.create_superuser(phone='9999999999', user_type='ADMIN', password='admin123')"

# 10. Start FastAPI server (serves everything on port 8000)
python run.py

# 11. (Optional) Run Celery worker in a separate terminal
celery -A docconnect_backend worker -l info
```

### 14.3 All URLs

| URL | Description |
|-----|-------------|
| http://localhost:8000/ | API root |
| http://localhost:8000/api/docs | Swagger UI (interactive API docs) |
| http://localhost:8000/api/redoc | ReDoc API docs |
| http://localhost:8000/api/openapi.json | OpenAPI schema |
| http://localhost:8000/health | Health check |
| http://localhost:8000/admin/ | Django Admin panel |

### 14.4 Super Admin Credentials

| Field | Value |
|-------|-------|
| Phone | `9999999999` |
| Password | `admin123` |
| User Type | `ADMIN` |

> **Note:** Change password immediately in production via Django Admin → Users.

### 14.5 Python 3.14 Compatibility Notes

If you are on Python 3.14 (Windows), the following pinned versions are required in `requirements.txt` — they ship pre-built wheels for 3.14:

```
pydantic[email]==2.13.4
pydantic-core==2.46.4
psycopg[binary]==3.3.4
fastapi==0.115.12
uvicorn[standard]==0.34.3
```

### 14.6 Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up -d --build

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# View logs
docker-compose logs -f
```

---

## 15. Deployment

### 15.1 Environment Variables

```bash
# .env.example

# Django
DJANGO_SECRET_KEY=your-secret-key-min-50-chars
DEBUG=False
ALLOWED_HOSTS=api.docconnect.com,www.docconnect.com
DJANGO_SETTINGS_MODULE=docconnect_backend.settings.production

# Database
DB_NAME=docconnect_db
DB_USER=docconnect_user
DB_PASSWORD=your-db-password
DB_HOST=postgres
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/2

# AWS S3
AWS_ACCESS_KEY_ID=<aws-access-key>
AWS_SECRET_ACCESS_KEY=<aws-secret-key>
AWS_STORAGE_BUCKET_NAME=docconnect-media
AWS_S3_REGION_NAME=ap-south-1
AWS_S3_CUSTOM_DOMAIN=cdn.docconnect.com   # optional CloudFront

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=<email>
EMAIL_HOST_PASSWORD=<app-password>
DEFAULT_FROM_EMAIL=noreply@docconnect.com

# SMS (e.g. MSG91 / Twilio)
SMS_PROVIDER=msg91                         # msg91 | twilio
SMS_API_KEY=<sms-api-key>
SMS_SENDER_ID=DOCCON
SMS_OTP_TEMPLATE_ID=<template-id>

# Firebase (Push Notifications)
FCM_SERVER_KEY=<fcm-server-key>

# Sentry
SENTRY_DSN=<sentry-dsn>
SENTRY_ENVIRONMENT=production

# JWT
JWT_SECRET_KEY=<jwt-secret-min-32-chars>
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=30

# NMC Verification API (optional)
NMC_API_BASE_URL=https://api.nmc.org.in
NMC_API_KEY=<nmc-api-key>
```

### 15.2 Production Deployment

```bash
# Build production Docker images
docker-compose -f docker-compose.production.yml build

# Push to registry
docker tag docconnect-backend:latest your-registry/docconnect-backend:latest
docker push your-registry/docconnect-backend:latest

# Deploy to server
ssh user@your-server
docker pull your-registry/docconnect-backend:latest
docker-compose -f docker-compose.production.yml up -d

# Run migrations
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate

# Collect static files
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
```

---

## 16. API Documentation

### 16.1 Access Swagger UI

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/openapi.json`

### 16.2 Complete API Reference

> All endpoints are documented in Sections 2–5 per module. Use Swagger UI at `/api/docs` for interactive reference.

---

## 17. Security
| POST | `/api/v1/auth/register/` | Register with phone + password |
| POST | `/api/v1/auth/login/` | Login with phone + password |
| POST | `/api/v1/auth/send-otp/` | Send OTP to phone |
| POST | `/api/v1/auth/verify-otp/` | Verify OTP and get tokens |
| POST | `/api/v1/auth/refresh/` | Refresh JWT token |
| POST | `/api/v1/auth/logout/` | Logout / blacklist token |
| POST | `/api/v1/auth/password/forgot/` | Forgot password — send reset challenge |
| POST | `/api/v1/auth/password/reset/` | Reset password with token |
| POST | `/api/v1/auth/password/change/` | Change password (authenticated) |
| GET | `/api/v1/auth/sessions/` | List active sessions / devices |
| DELETE | `/api/v1/auth/sessions/{id}/` | Revoke a specific session |
| POST | `/api/v1/auth/sessions/revoke-all/` | Revoke all sessions |
| DELETE | `/api/v1/account/` | Deactivate / delete account |
| **Doctors** | | |
| POST | `/api/v1/doctors/profile/` | Create doctor profile |
| GET | `/api/v1/doctors/profile/me/` | Get my profile |
| PATCH | `/api/v1/doctors/profile/me/` | Update my profile |
| GET | `/api/v1/doctors/profile/{id}/` | View any doctor's profile |
| POST | `/api/v1/doctors/profile/me/photo/` | Upload profile photo |
| GET | `/api/v1/doctors/search/` | Search doctors |
| POST | `/api/v1/doctors/profile/me/registrations/` | Add NMC registration |
| GET | `/api/v1/doctors/profile/me/registrations/` | List registrations |
| POST | `/api/v1/doctors/profile/me/qualifications/` | Add qualification |
| GET | `/api/v1/doctors/profile/me/qualifications/` | List qualifications |
| DELETE | `/api/v1/doctors/profile/me/qualifications/{id}/` | Delete qualification |
| POST | `/api/v1/doctors/profile/me/experiences/` | Add experience |
| GET | `/api/v1/doctors/profile/me/experiences/` | List experiences |
| PATCH | `/api/v1/doctors/profile/me/experiences/{id}/` | Update experience |
| DELETE | `/api/v1/doctors/profile/me/experiences/{id}/` | Delete experience |
| POST | `/api/v1/doctors/profile/me/affiliations/` | Add hospital affiliation |
| GET | `/api/v1/doctors/profile/me/affiliations/` | List affiliations |
| PATCH | `/api/v1/doctors/profile/me/affiliations/{id}/` | Update affiliation |
| DELETE | `/api/v1/doctors/profile/me/affiliations/{id}/` | Delete affiliation |
| GET | `/api/v1/doctors/profile/me/verification/` | Get verification status |
| POST | `/api/v1/doctors/profile/me/verification/submit/` | Submit verification documents |
| POST | `/api/v1/doctors/profile/me/verification/resubmit/` | Resubmit after rejection |
| GET | `/api/v1/doctors/profile/me/status/` | Get professional status |
| PUT | `/api/v1/doctors/profile/me/status/` | Update professional status |
| GET | `/api/v1/doctors/profile/me/privacy/` | Get privacy settings |
| PUT | `/api/v1/doctors/profile/me/privacy/` | Update privacy settings |
| **Files** | | |
| POST | `/api/v1/files/upload/` | Upload file (photo/CV/credential) |
| GET | `/api/v1/files/{id}/` | Get file metadata |
| GET | `/api/v1/files/{id}/signed-url/` | Get expiring signed URL for file |
| DELETE | `/api/v1/files/{id}/` | Delete file |
| **Search** | | |
| GET | `/api/v1/search/doctors/` | Search doctors (advanced filters) |
| GET | `/api/v1/search/hospitals/` | Search hospitals |
| GET | `/api/v1/search/jobs/` | Search jobs |
| GET | `/api/v1/search/communities/` | Search specialty communities |
| GET | `/api/v1/search/universal/` | Universal search (doctors/hospitals/jobs/communities) |
| **Network** | | |
| POST | `/api/v1/network/connections/request/` | Send connection request |
| POST | `/api/v1/network/connections/{id}/accept/` | Accept connection |
| POST | `/api/v1/network/connections/{id}/reject/` | Reject connection |
| DELETE | `/api/v1/network/connections/{id}/` | Remove connection |
| GET | `/api/v1/network/connections/` | List connections / requests |
| POST | `/api/v1/network/follow/{user_id}/` | Follow a user |
| DELETE | `/api/v1/network/follow/{user_id}/` | Unfollow a user |
| POST | `/api/v1/network/block/{user_id}/` | Block a user |
| DELETE | `/api/v1/network/block/{user_id}/` | Unblock a user |
| GET | `/api/v1/network/blocked/` | List blocked users |
| POST | `/api/v1/reports/` | Report a profile/post/comment/job/hospital |
| **Feed & Posts** | | |
| GET | `/api/v1/feed/home/` | Home summary |
| GET | `/api/v1/feed/` | Paginated feed posts |
| POST | `/api/v1/feed/posts/` | Create post |
| PATCH | `/api/v1/feed/posts/{id}/` | Edit own post |
| DELETE | `/api/v1/feed/posts/{id}/` | Delete own post |
| POST | `/api/v1/feed/posts/{id}/like/` | Like / unlike a post |
| GET | `/api/v1/feed/posts/{id}/comments/` | Get comments |
| POST | `/api/v1/feed/posts/{id}/comments/` | Add comment |
| PATCH | `/api/v1/feed/comments/{id}/` | Edit comment / reply |
| DELETE | `/api/v1/feed/comments/{id}/` | Delete comment / reply |
| POST | `/api/v1/feed/comments/{id}/reply/` | Reply to comment |
| **Communities** | | |
| GET | `/api/v1/communities/` | List specialty communities |
| GET | `/api/v1/communities/{id}/` | Community detail |
| POST | `/api/v1/communities/{id}/join/` | Join community |
| DELETE | `/api/v1/communities/{id}/leave/` | Leave community |
| GET | `/api/v1/communities/{id}/posts/` | Community posts |
| POST | `/api/v1/communities/{id}/posts/` | Post in community |
| **Hospitals** | | |
| POST | `/api/v1/hospitals/register/` | Register new hospital |
| GET | `/api/v1/hospitals/me/` | Get my hospital profile |
| PATCH | `/api/v1/hospitals/me/` | Update hospital profile |
| POST | `/api/v1/hospitals/me/verification/submit/` | Submit hospital verification documents |
| GET | `/api/v1/hospitals/me/verification/` | Get hospital verification status |
| POST | `/api/v1/hospitals/me/branches/` | Add branch |
| GET | `/api/v1/hospitals/me/branches/` | List branches |
| PATCH | `/api/v1/hospitals/me/branches/{id}/` | Update branch |
| DELETE | `/api/v1/hospitals/me/branches/{id}/` | Deactivate branch |
| POST | `/api/v1/hospitals/me/departments/` | Add department |
| GET | `/api/v1/hospitals/me/departments/` | List departments |
| POST | `/api/v1/hospitals/me/users/` | Add hospital user |
| GET | `/api/v1/hospitals/me/users/` | List hospital users |
| PATCH | `/api/v1/hospitals/me/users/{id}/` | Update user role/branch/status |
| DELETE | `/api/v1/hospitals/me/users/{id}/` | Revoke user membership |
| POST | `/api/v1/hospitals/me/invite-user/` | Invite HR / Recruiter |
| GET | `/api/v1/hospitals/me/staff/` | List staff |
| POST | `/api/v1/hospitals/me/upload-logo/` | Upload logo |
| GET | `/api/v1/hospitals/{id}/` | View public hospital profile |
| **Jobs** | | |
| POST | `/api/v1/jobs/` | Create job posting |
| PATCH | `/api/v1/jobs/{id}/` | Update job posting |
| POST | `/api/v1/jobs/{id}/publish/` | Publish a draft job |
| POST | `/api/v1/jobs/{id}/close/` | Close a job posting |
| GET | `/api/v1/jobs/` | List jobs |
| GET | `/api/v1/jobs/{id}/` | Get job details |
| POST | `/api/v1/jobs/{id}/save/` | Save a job |
| DELETE | `/api/v1/jobs/{id}/save/` | Unsave a job |
| GET | `/api/v1/doctors/me/saved-jobs/` | List saved jobs |
| GET | `/api/v1/jobs/my-applications/` | My applications |
| POST | `/api/v1/jobs/{id}/apply/` | Apply to job |
| POST | `/api/v1/jobs/{id}/withdraw/` | Withdraw application |
| GET | `/api/v1/jobs/{id}/applications/` | View applicants |
| PATCH | `/api/v1/jobs/applications/{id}/status/` | Update application status |
| POST | `/api/v1/applications/{id}/notes/` | Add internal note |
| GET | `/api/v1/applications/{id}/notes/` | List application notes |
| POST | `/api/v1/applications/{id}/interview/` | Schedule interview |
| PATCH | `/api/v1/applications/{id}/interview/{interview_id}/` | Update interview outcome |
| POST | `/api/v1/applications/{id}/offer/` | Send offer |
| POST | `/api/v1/applications/{id}/invite/` | Invite doctor to apply |
| GET | `/api/v1/jobs/{id}/matches/` | Get matched doctors for a job |
| GET | `/api/v1/doctors/me/job-recommendations/` | Get recommended jobs for doctor |
| **Master Data** | | |
| GET | `/api/v1/masters/specialties/` | List specialties |
| GET | `/api/v1/masters/qualifications/` | List qualifications |
| GET | `/api/v1/masters/job-types/` | List job types |
| GET | `/api/v1/masters/shift-types/` | List shift types |
| **Availability** | | |
| POST | `/api/v1/availability/` | Post availability |
| GET | `/api/v1/availability/me/` | List my availabilities |
| PATCH | `/api/v1/availability/{id}/` | Update availability |
| DELETE | `/api/v1/availability/{id}/` | Deactivate availability |
| GET | `/api/v1/availability/{id}/slots/` | List slots |
| POST | `/api/v1/availability/{id}/slots/` | Add slot |
| PATCH | `/api/v1/availability/slots/{slot_id}/` | Update a slot |
| DELETE | `/api/v1/availability/slots/{slot_id}/` | Delete a slot |
| GET | `/api/v1/availability/preferences/` | Get availability preferences |
| PUT | `/api/v1/availability/preferences/` | Update availability preferences |
| **Shifts** | | |
| POST | `/api/v1/shifts/requirements/` | Post shift requirement |
| GET | `/api/v1/shifts/requirements/` | List open requirements |
| PATCH | `/api/v1/shifts/requirements/{id}/` | Update shift requirement |
| GET | `/api/v1/shifts/requirements/mine/` | My hospital's requirements |
| POST | `/api/v1/shifts/requirements/{id}/match/` | Get matched doctors |
| GET | `/api/v1/shifts/requirements/{id}/matched-doctors/` | Get matched doctors |
| POST | `/api/v1/shifts/requirements/{id}/request/` | Doctor requests shift |
| PATCH | `/api/v1/shifts/requests/{id}/respond/` | Doctor accepts/declines |
| PATCH | `/api/v1/shifts/requests/{id}/confirm/` | Hospital confirms |
| PATCH | `/api/v1/shifts/requests/{id}/complete/` | Mark completed |
| PATCH | `/api/v1/shifts/requests/{id}/cancel/` | Cancel request |
| GET | `/api/v1/shifts/requests/{id}/history/` | Shift request state history |
| GET | `/api/v1/shifts/requests/mine/` | My shift requests |
| **Messaging** | | |
| POST | `/api/v1/messages/conversations/` | Start conversation |
| GET | `/api/v1/messages/conversations/` | List conversations |
| GET | `/api/v1/messages/conversations/{id}/messages/` | Get messages |
| POST | `/api/v1/messages/conversations/{id}/messages/` | Send message |
| POST | `/api/v1/messages/conversations/{id}/read/` | Mark conversation as read |
| POST | `/api/v1/messages/conversations/{id}/report/` | Report conversation |
| POST | `/api/v1/messages/conversations/{id}/block/` | Block conversation |
| DELETE | `/api/v1/messages/conversations/{id}/block/` | Unblock conversation |
| **Devices & Notifications** | | |
| POST | `/api/v1/devices/` | Register device for push notifications |
| DELETE | `/api/v1/devices/{id}/` | Revoke device token |
| GET | `/api/v1/notifications/` | List notifications |
| GET | `/api/v1/notifications/unread-count/` | Unread count |
| PATCH | `/api/v1/notifications/{id}/read/` | Mark as read |
| POST | `/api/v1/notifications/read-all/` | Mark all as read |
| GET | `/api/v1/notification-preferences/` | Get notification preferences |
| PUT | `/api/v1/notification-preferences/` | Update notification preferences |
| **Admin CRM** | | |
| GET | `/api/v1/admin/dashboard/` | Platform overview metrics |
| GET | `/api/v1/admin/doctors/verification-queue/` | Doctor verification queue |
| GET | `/api/v1/admin/doctors/verification-cases/{id}/` | Verification case detail |
| POST | `/api/v1/admin/doctors/verification-cases/{id}/approve/` | Approve doctor verification |
| POST | `/api/v1/admin/doctors/verification-cases/{id}/reject/` | Reject doctor verification |
| POST | `/api/v1/admin/doctors/verification-cases/{id}/resubmit/` | Allow resubmission |
| GET | `/api/v1/admin/hospitals/verification-queue/` | Hospital verification queue |
| POST | `/api/v1/admin/hospitals/verification-cases/{id}/approve/` | Approve hospital verification |
| POST | `/api/v1/admin/hospitals/verification-cases/{id}/reject/` | Reject hospital verification |
| GET | `/api/v1/admin/users/` | List all users |
| POST | `/api/v1/admin/users/{id}/restrict/` | Restrict user |
| POST | `/api/v1/admin/users/{id}/suspend/` | Suspend user |
| POST | `/api/v1/admin/users/{id}/restore/` | Restore user |
| POST | `/api/v1/admin/users/{id}/deactivate/` | Deactivate user |
| GET | `/api/v1/admin/reports/` | Reports queue |
| GET | `/api/v1/admin/reports/{id}/` | Report detail |
| POST | `/api/v1/admin/reports/{id}/action/` | Action a report |
| POST | `/api/v1/admin/reports/{id}/dismiss/` | Dismiss a report |
| POST | `/api/v1/admin/reports/{id}/escalate/` | Escalate a report |
| POST | `/api/v1/admin/posts/{id}/moderate/` | Moderate a post |
| POST | `/api/v1/admin/jobs/{id}/moderate/` | Moderate a job |
| POST | `/api/v1/admin/communities/` | Create specialty community |
| PATCH | `/api/v1/admin/communities/{id}/` | Update community |
| POST | `/api/v1/admin/communities/{id}/archive/` | Archive community |
| GET | `/api/v1/admin/audit-logs/` | Audit log records |
| GET | `/api/v1/admin/analytics/overview/` | Analytics overview |
| **Support** | | |
| POST | `/api/v1/support/tickets/` | Create support ticket |
| GET | `/api/v1/support/tickets/` | List my support tickets |
| GET | `/api/v1/support/tickets/{id}/` | Ticket detail + messages |
| POST | `/api/v1/support/tickets/{id}/messages/` | Add message to ticket |
| PATCH | `/api/v1/admin/support/tickets/{id}/` | Update ticket status (admin) |
| POST | `/api/v1/admin/support/tickets/{id}/resolve/` | Resolve ticket |
| **Billing** | | |
| GET | `/api/v1/billing/plans/` | List billing plans |
| GET | `/api/v1/billing/subscription/` | Current hospital subscription |
| POST | `/api/v1/billing/subscription/` | Subscribe to a plan |
| PATCH | `/api/v1/billing/subscription/` | Update/cancel subscription |
| GET | `/api/v1/billing/invoices/` | List invoices |
| GET | `/api/v1/billing/invoices/{id}/` | Invoice detail |
| POST | `/api/v1/billing/webhooks/{provider}/` | Payment webhook (idempotent) |


### 17.1 Authentication Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  Client │────▶│  Send   │────▶│  Verify │────▶│  JWT    │
│         │     │  OTP    │     │  OTP    │     │  Tokens │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
                                                       │
                                                       ▼
                                              ┌─────────────┐
                                              │  API Calls  │
                                              │  with JWT   │
                                              └─────────────┘
```

### 17.2 Security Features

- HTTPS enforced via `HTTPSRedirectMiddleware` + nginx SSL termination
- Rate limiting via `slowapi` on auth, search, messaging and report endpoints
- CORS restricted to allowed origins in production
- Trusted host middleware enabled in production
- Data encryption for sensitive fields via `apps/core/services/encryption.py` (Fernet/AES-256)

### 17.3 Data Encryption

Sensitive fields are encrypted at rest using `DataEncryption` in `apps/core/services/encryption.py`. The encryption key is sourced from `DJANGO_SECRET_KEY` via environment variable — never hardcoded.

---

## 18. Testing

### 18.1 Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=fastapi_app --cov=apps tests/

# Generate coverage report
pytest --cov=fastapi_app --cov=apps --cov-report=html tests/
```

### 18.2 Test Coverage

See `tests/` directory for full test suite including:
- `test_auth.py` — OTP, login, token rotation
- `test_doctors.py` — Profile, verification, search
- `test_jobs.py` — Job posting, apply, pipeline
- `test_availability.py` — Slots, shift lifecycle
- `test_security_rbac.py` — 21 RBAC scenarios (see Section 21H)

---

## 19. Troubleshooting

### 19.1 Common Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| `django.db.utils.OperationalError` | PostgreSQL not running | `sudo service postgresql start` |
| `ModuleNotFoundError: No module named 'django'` | Virtualenv not activated | `source venv/bin/activate` |
| FastAPI returns 401 on all requests | JWT secret mismatch | Ensure `JWT_SECRET_KEY` matches in `.env` |
| Celery tasks not executing | Redis not running | `redis-server` or `docker-compose up redis` |
| `postgis` extension missing | PostGIS not installed | `sudo apt install postgresql-16-postgis-3` |
| OTP SMS not delivered | Invalid `SMS_API_KEY` | Check provider dashboard for key validity |

### 19.2 Logs

```bash
# Django logs
docker-compose logs backend

# FastAPI logs
docker-compose logs fastapi

# Celery logs
docker-compose logs celery

# All services
docker-compose logs -f
```

---

## 20. Roadmap

### Phase 1 — MVP (Current ✅)
- [x] Phone + password registration & login
- [x] OTP-based authentication
- [x] JWT session management with refresh rotation & revocation
- [x] Doctor profile with NMC verification (UNVERIFIED → PENDING → VERIFIED → REJECTED → RESUBMISSION)
- [x] Doctor qualifications, experience & hospital affiliations
- [x] Doctor professional status & privacy settings
- [x] Doctor search (name / specialty / city / experience)
- [x] Feed posts (UPDATE / CASE / ARTICLE / PHOTO) with patient-privacy confirmation
- [x] Post likes, comments & threaded replies
- [x] Doctor connections (send / accept / decline / withdraw)
- [x] Follow / unfollow users
- [x] Block / unblock users
- [x] Home summary API (stats, urgent jobs, suggested doctors)
- [x] Hospital follow
- [x] Hospital registration, branches, departments, staff (ADMIN/HR/RECRUITER roles)
- [x] Hospital verification workflow
- [x] Job posting (DRAFT → PUBLISHED → CLOSED) & one-tap apply
- [x] Job save / unsave
- [x] Recruitment CRM pipeline with full history log (notes, interview, offer)
- [x] Doctor availability & slot management
- [x] Availability preferences
- [x] Shift requirements & full shift lifecycle (request/accept/confirm/complete/cancel)
- [x] Shift state history
- [x] Doctor-shift matching algorithm (configurable weights via matching_configs)
- [x] Job-doctor matching with score components & reasons
- [x] Direct messaging (conversations + messages)
- [x] Messaging read receipts, block/report conversation
- [x] Device token registration for push notifications
- [x] Notifications (list, read, unread count, preferences)
- [x] File upload with signed URLs (photos, logos, credentials)
- [x] Universal search (doctors / hospitals / jobs / communities)
- [x] Reports — DB-backed `Report` model with severity, reason codes, lifecycle
- [x] Django Admin panel
- [x] Docker Compose setup
- [x] Admin CRM — verification queues with turnaround time
- [x] Admin CRM — user management (restrict/suspend/restore/deactivate) with reason + AuditLog
- [x] Admin CRM — content moderation (posts/jobs) with reason + AuditLog
- [x] Admin CRM — reports queue with severity/target_type filters + action/dismiss/escalate
- [x] Admin CRM — community management with AuditLog
- [x] Admin CRM — audit logs with action/target_type filters
- [x] Admin CRM — full operational analytics (turnaround, funnel, shift rates, resolution time)
- [x] Admin CRM — support tickets (DB-backed SupportTicket/SupportMessage, internal notes)
- [x] Admin CRM — matching config management (versioned weights, activate)
- [x] Admin CRM — settings CRUD (specialties, qualifications)
- [x] Admin CRM — Super Admin endpoints (create/deactivate/update-permissions for admin users)
- [x] Admin CRM — hospital verification case detail endpoint
- [x] Admin CRM — user detail endpoint
- [x] Admin CRM — support ticket assign endpoint
- [x] Module 6 — Doctor Mobile App spec: navigation, onboarding flow, verification-gated actions
- [x] Module 6 — `languages` + `career_preferences` fields on DoctorProfile
- [x] Module 6 — CASE post patient-privacy confirmation required (`patient_privacy_confirmed`)
- [x] Module 6 — Server-side PII detection on posts (phone/Aadhaar/email/patient ID)
- [x] Module 6 — `match_score` + `match_factors` returned on job list for doctors
- [x] Module 6 — Slot overlap check against accepted/confirmed shifts (409)
- [x] Module 6 — Deactivate availability blocked if active shift requests exist (409)
- [x] Module 6 — Account deletion cascades: withdraw applications, deactivate availability, cancel shift requests
- [x] Spec 02 — `DoctorAffiliation` model with proper DB table (replaces JSONB metadata)
- [x] Spec 02 — `Follow` model (DB-backed doctor/hospital follow relationship)
- [x] Spec 02 — `Block` model (DB-backed user block; replaces metadata array)
- [x] Spec 02 — `JobSave` model (DB-backed job saves; replaces metadata array)
- [x] Spec 02 — `ShiftStatusHistory` model (immutable shift state audit trail)
- [x] Spec 02 — `DeviceToken` model (FCM/APNs push tokens per device)
- [x] Spec 02 — `NotificationPreference` model (per-user per-event channel preferences)
- [x] Spec 02 — `Plan` / `Subscription` / `Entitlement` billing models
- [x] Spec 02 — `Invoice` / `Payment` billing models with provider ID + refund tracking
- [x] Spec 02 — Privacy enforcement rules documented and enforced at query/serialization layer
- [x] Spec 02 — Security & infrastructure checklist documented
- [x] Spec 02 — API contract standard (method, auth role, schema, errors, pagination, side effects, audit event)
- [x] Gap Audit — `is_super_admin` field on `User` model (explicit Platform Admin vs Super Admin distinction)
- [x] Gap Audit — `require_super_admin()` dependency in `dependencies.py` (separate from `require_admin()`)
- [x] Gap Audit — Super Admin endpoints: create/deactivate/update-permissions for admin users (`/api/v1/admin/super/admin-users/`)
- [x] Gap Audit — Matching config create + activate restricted to Super Admin only
- [x] Gap Audit — Super Admin self-deactivation blocked (400)
- [x] Gap Audit — Platform Admin cannot touch Super Admin accounts (403)
- [x] Gap Audit — `permissions` JSONField on `HospitalUser` for custom per-user permission overrides
- [x] Gap Audit — `ReportEvidence` model (`report_evidence` table) with private S3 file reference
- [x] Gap Audit — `create_admin.py` production credential guard (blocks default phone/password in `DJANGO_ENV=production`)
- [x] Gap Audit — `create_admin.py` `--super` flag to set `is_super_admin=True`
- [x] Gap Audit — Security/RBAC test suite (`tests/test_security_rbac.py`) covering 13 audit scenarios
- [x] Gap Audit — Community moderators deferred to Phase 2 (documented below)
- [x] Gap Audit — Geospatial: JSONB coordinates used for V1; PostGIS `PointField` deferred to Phase 2
- [x] Gap Audit — Base64 fields (`photo_base64`, `cover_base64`, `logo_base64`) marked deprecated; production path is `file_id` + S3
- [x] Billing — plans, subscription, invoices, webhooks, refunds (Hospital Admin only)
- [x] Support — user tickets, admin ticket management, internal notes, assign, resolve
- [x] Masters — specialties, qualifications, councils, job types, shift types
- [x] Communities — list, join/leave, posts (Phase 2: moderators)
- [x] Candidate discovery — hospital HR can search/filter doctors with availability filters

### Phase 2 — Q3 2025 ✅ Implemented
- [x] Community moderator add/remove APIs — `POST/DELETE /api/v1/admin/communities/{id}/moderators/`, `CommunityMember.is_moderator` field, migration `core/0007`
- [x] Geospatial radius search (Haversine/JSONB) — `GET /api/v1/search/doctors/nearby/` + `GET /api/v1/search/hospitals/nearby/`
- [x] WebSocket real-time messaging — Django Channels 4.1, `channels-redis`, `apps/messaging/consumers.py`, `routing.py`, ASGI updated
- [x] Super Admin MFA/2FA (TOTP via `pyotp`) — `fastapi_app/routers/mfa.py`: setup, verify, login, disable, status endpoints; `User.totp_secret` + `User.mfa_enabled` fields, migration `accounts/0004`
- [x] iOS APNs push notification support — `devices.py` rewritten to use `DeviceToken` DB model; `platform: APNS` accepted, `bundle_id` field, update-on-re-register logic, `GET /api/v1/devices/` list endpoint; migration `notifications/0004`
- [x] Hospital verification via document OCR — `apps/core/services/ocr.py` (AWS Textract); `POST /api/v1/admin/hospitals/verification-cases/{id}/ocr/` extracts text + fields; `POST .../ocr/confirm/` approves after review; audit logged; graceful fallback in dev mode
- [x] PostGIS `PointField` geospatial — `USE_POSTGIS=true` enables `django.contrib.gis` + `PointField(srid=4326, geography=True)` on `DoctorProfile` and `Hospital`; migrations `doctors/0014` + `hospitals/0007` run `CREATE EXTENSION IF NOT EXISTS postgis` + `AlterField`; JSONB Haversine fallback preserved when disabled
- [x] Specialty communities group discussions UI — backend API complete (`GET/POST /api/v1/communities/{id}/posts/`); frontend/mobile UI deferred to Phase 3

### Phase 3 — Q4 2026
- [x] CME credit tracking — `CMEEvent` + `CMECredit` models; `GET/POST /api/v1/cme/events/`, `GET/POST/DELETE /api/v1/cme/credits/`, `GET /api/v1/cme/credits/summary/`; migration `core/0008`
- [x] Billing & subscription management (feature-flagged) — `Plan`/`Subscription`/`Entitlement`/`Invoice`/`Payment` models + full billing router already implemented
- [x] Peer endorsements & skill recommendations — `Endorsement` model; `POST /api/v1/endorsements/`, `GET /api/v1/endorsements/received/{doctor_id}/`, skill summary + delete; migration `core/0008`
- [x] Second opinion & case referral network — `SecondOpinionRequest` model; `POST /api/v1/second-opinions/`, sent/received lists, respond, complete, cancel; migration `core/0008`
- [x] Hospital analytics dashboard (applications, hires, shift fill rate) — `HospitalAnalyticsSnapshot` model + live aggregation; `GET /api/v1/analytics/hospital/dashboard/`, `GET /api/v1/analytics/hospital/snapshots/`; migration `core/0008`
- [x] Multi-language support (English, Hindi, Tamil, Telugu) — `preferred_language` field on `DoctorProfile` (BCP-47: `en`/`hi`/`ta`/`te`); migration `doctors/0015`
- [x] Telemedicine / video consultation scheduling — `TelemedicineSession` model; `POST /api/v1/telemedicine/sessions/`, list, get, status update; migration `core/0008`

---

## 21. Gap Audit Final Report (Doc-Connect Backend Gap Audit)

> Audit completed against the **DOC-CONNECT — FINAL BACKEND GAP AUDIT & FIX REQUIREMENTS** specification.

### A. Already Implemented Correctly

| Item | Evidence |
|------|----------|
| Doctor verification workflow (UNVERIFIED→PENDING→VERIFIED→REJECTED→RESUBMISSION) | `DoctorProfile.verification_status` + admin endpoints |
| Hospital verification workflow | `Hospital.verification_status` + admin endpoints |
| `HospitalUser` model with `user`, `role`, `hospital_id`, `branch_id`, `department_id`, `permissions`, `status` | `apps/hospitals/models.py` + migration `0005` |
| Branch User architecture via `HospitalUser.role + branch_id` (no duplicate `user_type`) | Documented in Section 3.0 |
| Hospital scope isolation — `/me/` endpoints resolve hospital from authenticated user's `HospitalUser` | `fastapi_app/routers/hospitals.py` — `_get_active_admin_hu` / `_get_active_hu` |
| Inactive `HospitalUser` blocked — `status='ACTIVE'` enforced on every hospital endpoint | `_get_active_admin_hu` / `_get_active_hu` helpers |
| `Report` model with severity, reason codes, lifecycle, reviewer, resolution | `apps/core/models.py` |
| `ReportEvidence` model — private S3 file reference, never public | `apps/core/models.py` + migration `core/0005` |
| `AuditLog` model — immutable, written on every privileged action | `apps/core/models.py` + `admin.py` |
| JWT rotation + `RefreshSession` revocation | `apps/accounts/models.py` + `auth.py` router |
| Suspended/deleted user blocked at `get_current_user` | `fastapi_app/dependencies.py` |
| `MatchingConfig` — versioned weights, never hardcoded | `apps/core/models.py` |
| Billing models (`Plan`, `Subscription`, `Entitlement`, `Invoice`, `Payment`) | `apps/core/models.py` |
| `is_super_admin` field on `User` | `apps/accounts/models.py` + migration `accounts/0002` |
| `require_admin()` / `require_super_admin()` in `dependencies.py` | `fastapi_app/dependencies.py` |
| Super Admin endpoints (`/super/admin-users/`) | `fastapi_app/routers/admin.py` |
| Super Admin self-deactivation blocked (400) | `deactivate_admin_user` endpoint |
| Platform Admin cannot suspend/restrict/deactivate Super Admin (403) | `_update_user_status_with_audit` guard |
| `dismiss_report` / `escalate_report` FK assignment via `.save()` (not `.update()`) | `fastapi_app/routers/admin.py` |
| `create_admin.py` production credential guard | `scripts/create_admin.py` — `DJANGO_ENV=production` block |
| Billing 403 for non-HOSPITAL_ADMIN | `fastapi_app/routers/billing.py` |
| Hospital A cannot access Hospital B jobs/staff | `jobs.py` — `job__hospital=hu.hospital` scope check |
| `photo_base64`, `cover_base64`, `logo_base64` marked deprecated | `apps/doctors/models.py`, `apps/hospitals/models.py` |
| Community moderators deferred to Phase 2 with explicit code comment | `fastapi_app/routers/admin.py` |

### B. Partially Implemented → Completed

| Item | Gap Found | Fix Applied |
|------|-----------|-------------|
| `dismiss_report` / `escalate_report` | Used `.update()` with FK object — silently fails in Django | Changed to `.get()` + `.save()` with explicit field list |
| Platform Admin → Super Admin protection | `_update_user_status_with_audit` had no Super Admin guard | Added `if target.is_super_admin and not performed_by.is_super_admin: raise 403` |
| Community moderators documentation | README claimed "manage moderators" as live | Added Phase 2 note in admin.py and README |
| Base64 fields | No deprecation notice in models | Added `# DEPRECATED:` comments on all three base64 fields |

### C. Missing → Implemented

| Item | Implementation |
|------|----------------|
| RBAC tests: Platform Admin cannot suspend/restrict/deactivate Super Admin | `tests/test_security_rbac.py` — tests 19, 20 |
| RBAC test: Platform Admin cannot modify Super Admin permissions | `tests/test_security_rbac.py` — test 20 |
| RBAC test: Super Admin can suspend regular user | `tests/test_security_rbac.py` — test 21 |

### D. Intentionally Deferred (Phase 3)

| Item | Reason | Where Documented |
|------|--------|------------------|
| PostGIS `PointField` geospatial | V1 uses Haversine/JSONB; PostGIS requires `django.contrib.gis` + DB extension + data migration | README Section 10.4 + roadmap |
| Hospital verification via document OCR | Third-party OCR provider not yet selected | Phase 3 roadmap |
| CME credit tracking | Product spec not finalized | Phase 3 roadmap |
| Peer endorsements | Product spec not finalized | Phase 3 roadmap |

### E. Database Migrations Created

| Migration | App | Change |
|-----------|-----|--------|
| `accounts/0002_add_is_super_admin.py` | `accounts` | `is_super_admin BooleanField(default=False)` on `users` |
| `accounts/0004_add_mfa_fields.py` | `accounts` | `totp_secret CharField` + `mfa_enabled BooleanField` on `users` |
| `hospitals/0005_add_hospitaluser_permissions.py` | `hospitals` | `permissions JSONField(default=dict)` on `hospital_users` |
| `core/0005_add_report_evidence.py` | `core` | New `report_evidence` table |
| `core/0007_community_moderator_mfa.py` | `core` | `is_moderator BooleanField(default=False)` on `community_members` |

### F. APIs Added / Changed

| Method | Endpoint | Change |
|--------|----------|--------|
| POST | `/api/v1/admin/super/admin-users/` | Added — Super Admin creates Platform/Super Admin user |
| POST | `/api/v1/admin/super/admin-users/{id}/deactivate/` | Added — Super Admin deactivates admin user |
| PATCH | `/api/v1/admin/super/admin-users/{id}/permissions/` | Added — Super Admin updates `is_super_admin` flag |
| POST | `/api/v1/admin/matching-configs/` | Changed — requires Super Admin (not Platform Admin) |
| POST | `/api/v1/admin/matching-configs/{id}/activate/` | Changed — requires Super Admin (not Platform Admin) |
| GET | `/api/v1/billing/plans/` | Changed — requires `HOSPITAL_ADMIN` or `ADMIN`; HR/Doctor = 403 |

### G. Permission Changes

| Endpoint Group | Before | After |
|----------------|--------|-------|
| All admin endpoints | `user_type == 'ADMIN'` | `require_admin()` — Platform Admin or Super Admin |
| Matching config create/activate | Any admin | `require_super_admin()` — Super Admin only |
| Admin user management (`/super/`) | Not implemented | `require_super_admin()` — Super Admin only |
| Super Admin self-deactivation | Not guarded | Returns 400 |
| Platform Admin acting on Super Admin | Not guarded | Returns 403 |

### H. Security Tests Added

File: `tests/test_security_rbac.py` — 21 test cases total

| Test | Scenario |
|------|----------|
| `test_doctor_cannot_access_admin_dashboard` | Doctor → Admin API = 403 |
| `test_doctor_cannot_access_admin_users` | Doctor → Admin users list = 403 |
| `test_suspended_user_blocked` | Suspended user → protected API = 403 |
| `test_invalid_token_rejected` | Invalid token → 401 |
| `test_no_token_rejected` | No token → 403 |
| `test_platform_admin_cannot_create_admin_user` | Platform Admin → `/super/` = 403 |
| `test_platform_admin_cannot_activate_matching_config` | Platform Admin → matching config activate = 403 |
| `test_platform_admin_cannot_deactivate_admin_user` | Platform Admin → deactivate admin = 403 |
| `test_super_admin_can_access_dashboard` | Super Admin → dashboard = 200 |
| `test_super_admin_cannot_deactivate_own_account` | Super Admin self-deactivate = 400 |
| `test_hospital_a_cannot_access_hospital_b_staff` | Hospital A → Hospital B staff = not in results |
| `test_branch_user_identified_via_hospital_user` | Branch User = `HospitalUser.role + branch_id` |
| `test_hr_cannot_access_billing` | HR → billing = 403 |
| `test_revoked_refresh_token_rejected` | Revoked refresh → 401 |
| `test_report_evidence_model_exists` | `ReportEvidence` model + DB table exists |
| `test_user_has_is_super_admin_field` | `User.is_super_admin` field exists |
| `test_hospital_user_has_permissions_field` | `HospitalUser.permissions` field exists |
| `test_unauthenticated_doctor_search_blocked` | No token → search = 403 |
| `test_hr_cannot_access_billing_plans` | HR → `/billing/plans/` = 403 |
| `test_doctor_cannot_access_billing_plans` | Doctor → `/billing/plans/` = 403 |
| `test_hospital_a_cannot_access_hospital_b_jobs` | Hospital A → Hospital B job close = 403/404 |
| `test_inactive_hospital_user_cannot_manage_staff` | Inactive `HospitalUser` → staff management = 403 |
| `test_report_evidence_not_publicly_accessible` | Private evidence file → requires auth |
| `test_doctor_cannot_access_another_doctors_private_profile` | Doctor A → Doctor B private profile = 404/403 |
| `test_platform_admin_cannot_suspend_super_admin` | Platform Admin → suspend Super Admin = 403 |
| `test_platform_admin_cannot_restrict_super_admin` | Platform Admin → restrict Super Admin = 403 |
| `test_platform_admin_cannot_deactivate_super_admin` | Platform Admin → deactivate Super Admin = 403 |
| `test_platform_admin_cannot_modify_super_admin_permissions` | Platform Admin → modify Super Admin permissions = 403 |
| `test_super_admin_can_suspend_regular_user` | Super Admin → suspend regular user = 200 |

### I. Remaining Product Decisions

| Decision | Owner | Notes |
|----------|-------|-------|
| Community moderator workflow | Product | Define moderator role, permissions, add/remove flow before Phase 2 |
| PostGIS migration strategy | Engineering | Decide on `django.contrib.gis` adoption; requires DB extension + data migration for existing JSONB coordinates |
| Super Admin MFA/2FA provider | Engineering/Security | Select TOTP library (e.g. `pyotp`) or SMS 2FA; required before production Super Admin accounts |
| Custom `HospitalUser.permissions` schema | Product | Define allowed permission keys and values before enabling custom permission overrides |
| Sensitive data export approval chain | Product/Legal | Define who approves exports, what data is exportable, audit requirements |
| Base64 field deprecation timeline | Engineering | Set a migration deadline for clients still using `photo_base64`/`cover_base64`/`logo_base64` |

---

## 22. Contributing

### 22.1 Development Guidelines

1. **Code Style**
   - Python: Black, isort, flake8
   - Use type hints
   - Write docstrings

2. **Branch Strategy**
   - `main` - Production
   - `develop` - Development
   - `feature/*` - New features
   - `fix/*` - Bug fixes

3. **Commit Messages**
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation
   - `test:` Tests
   - `refactor:` Code refactor

### 22.2 Pull Request Process

1. Fork the repository
2. Create feature branch
3. Write tests
4. Update documentation
5. Submit pull request

---

## License

This project is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

---

## Contact

- **Email**: support@docconnect.com
- **Website**: https://docconnect.com
- **GitHub**: https://github.com/pkdubey/docconnect

---

**DocConnect — Building Trusted Doctor Professional Network**

---

*Last updated: July 2025 | Version 2.4 | Maintained by Pavan Kumar Dubey*