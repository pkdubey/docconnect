# DocConnect — Verified Professional Network for Doctors

> LinkedIn for Doctors — Verified identities, doctor-only jobs, clinical networking & locum marketplace.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python) ![Django](https://img.shields.io/badge/Django-5.0+-green?logo=django) ![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal?logo=fastapi) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue?logo=postgresql) ![Redis](https://img.shields.io/badge/Redis-7.2+-red?logo=redis) ![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker) ![License](https://img.shields.io/badge/License-Proprietary-red)

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Module 1 — Doctor Professional Network](#2-module-1--doctor-professional-network)
3. [Module 2 — Doctor Career Marketplace](#3-module-2--doctor-career-marketplace)
4. [Module 3 — Doctor Availability Exchange](#4-module-3--doctor-availability-exchange)
5. [System Architecture](#5-system-architecture)
6. [Technology Stack](#6-technology-stack)
7. [Database Design](#7-database-design)
8. [API Architecture (FastAPI)](#8-api-architecture-fastapi)
9. [Project Structure](#9-project-structure)
10. [Development Setup](#10-development-setup)
11. [Deployment](#11-deployment)
12. [API Documentation](#12-api-documentation)
13. [Security](#13-security)
14. [Testing](#14-testing)
15. [Troubleshooting](#15-troubleshooting)
16. [Roadmap](#16-roadmap)
17. [Contributing](#17-contributing)

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
| **Doctor Professional Network** | LinkedIn-style verified profiles, connections, feed, specialty communities, messaging | [Section 2](#2-module-1--doctor-professional-network) |
| **Doctor Career Marketplace** | Hospital onboarding, job posting, one-tap apply, recruitment CRM, AI matching | [Section 3](#3-module-2--doctor-career-marketplace) |
| **Doctor Availability Exchange** | Doctor availability, urgent shift requirements, doctor matching, shift lifecycle | [Section 4](#4-module-3--doctor-availability-exchange) |
| **Hospital Registration** | Verified hospital/clinic onboarding, branches, departments, staff management | [Section 3.1](#31-hospital-onboarding) |

### 1.3 Target Users

- **Individual Doctors** - MBBS, MD/MS, DM/MCh, dentists, AYUSH practitioners
- **Hospitals & Clinics** - Verified institutional accounts for hiring
- **Medical Institutions & NGOs** - CME events, fellowship postings

### 1.4 Why Django 5.0+ with FastAPI?

```
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐          ┌────────────────────────┐  │
│  │    Django 5.0+   │          │       FastAPI          │  │
│  │  (Admin, ORM,    │◄────────►│  (High-Performance     │  │
│  │   Models, Auth)  │          │   REST API Layer)      │  │
│  └──────────────────┘          └────────────────────────┘  │
│                                                             │
│  • PostgreSQL 16+ with advanced features                   │
│  • Async support for high-performance APIs                 │
│  • Automatic OpenAPI/Swagger documentation                 │
│  • Type safety with Pydantic                              │
│  • Django Admin for content management                    │
│  • Django ORM for database operations                     │
└─────────────────────────────────────────────────────────────┘
```

### 1.5 Quick Start (TL;DR)

```bash
git clone https://github.com/yourusername/docconnect.git && cd docconnect
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

**Super Admin Credentials (local dev):**

| Field | Value |
|-------|-------|
| Phone | `9999999999` |
| Password | `admin123` |
| User Type | `ADMIN` |

> To create superuser manually:
> ```bash
> python -c "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','docconnect_backend.settings.development'); django.setup(); from apps.accounts.models import User; User.objects.create_superuser(phone='9999999999', user_type='ADMIN', password='admin123')"
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
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  BANNER  (gradient / custom image)                       │  │
│  │  ┌──────┐  Dr. Arjun Sharma                              │  │
│  │  │ 👨‍⚕️  │  Cardiologist · 12 yrs exp                     │  │
│  │  │ Photo│  AIIMS Delhi · Mumbai                          │  │
│  │  └──────┘  ✅ NMC Verified  🟢 Open to Opportunities     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  About          Qualifications      Experience                  │
│  Specialization Clinical Interests  Registrations              │
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
| Feed / Posts | 🔜 Phase 2 | Clinical case sharing, articles, updates |
| Connections | 🔜 Phase 2 | Send / accept / withdraw connection requests |
| Endorsements | 🔜 Phase 2 | Peer skill endorsements |

### 2.4 Specialty Communities

| Feature | Status | Description |
|---------|--------|-------------|
| Specialty Groups | 🔜 Phase 2 | Cardiology, Neurology, Pediatrics etc. |
| Case Discussions | 🔜 Phase 2 | Anonymised clinical case sharing |
| Second Opinions | 🔜 Phase 2 | Request peer review on complex cases |
| CME Events | 🔜 Phase 2 | Continuing Medical Education tracking |

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
| DELETE | `/api/v1/doctors/profile/me/experiences/{id}/` | Delete experience |
| POST | `/api/v1/messages/conversations/` | Start a conversation |
| GET | `/api/v1/messages/conversations/` | List my conversations |
| GET | `/api/v1/messages/conversations/{id}/messages/` | Get messages |
| POST | `/api/v1/messages/conversations/{id}/messages/` | Send a message |

---

## 3. Module 2 — Doctor Career Marketplace

> Hospital-side job posting + doctor-side one-tap apply + full recruitment CRM pipeline + AI matching (Phase 2).

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

**Job Post Fields:**

| Field | Options |
|-------|---------|
| `job_type` | `FULL_TIME` / `PART_TIME` / `VISITING` / `LOCUM` / `CONTRACT` |
| `shift_type` | `DAY` / `NIGHT` / `ROTATIONAL` / `FLEXIBLE` |
| `salary_visibility` | `PUBLIC` / `ON_REQUEST` / `HIDDEN` |
| `status` | `DRAFT` → `PUBLISHED` → `CLOSED` / `EXPIRED` / `FILLED` |
| `is_urgent` | Boolean — shows urgent badge |
| `positions` | Number of openings |
| `experience_min_years` | Minimum experience required |
| `closing_date` | Auto-expire date |

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

### 3.4 AI Matching (Phase 2)

```
┌─────────────────────────────────────────────────────────────┐
│                    AI MATCHING ENGINE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Job Requirements          Doctor Profile                   │
│  ┌──────────────┐          ┌──────────────┐                │
│  │ specialty_id │◄────────►│ primary_spec │  40%           │
│  │ experience   │◄────────►│ exp_years    │  25%           │
│  │ location     │◄────────►│ prof_location│  20%           │
│  │ qual_ids     │◄────────►│ qualifications│ 15%           │
│  └──────────────┘          └──────────────┘                │
│                                                             │
│  Output: match_score (0–100) returned in job listing API   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**API Endpoints — Career Marketplace:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/hospitals/register/` | Register new hospital |
| GET | `/api/v1/hospitals/me/` | Get my hospital profile |
| POST | `/api/v1/hospitals/me/branches/` | Add hospital branch |
| GET | `/api/v1/hospitals/me/branches/` | List branches |
| POST | `/api/v1/hospitals/me/departments/` | Add department |
| GET | `/api/v1/hospitals/me/departments/` | List departments |
| POST | `/api/v1/hospitals/me/invite-user/` | Invite HR / Recruiter |
| GET | `/api/v1/hospitals/me/staff/` | List hospital staff |
| POST | `/api/v1/hospitals/me/upload-logo/` | Upload hospital logo |
| POST | `/api/v1/jobs/` | Create job posting |
| GET | `/api/v1/jobs/` | List jobs (with filters) |
| GET | `/api/v1/jobs/{id}/` | Get job details |
| POST | `/api/v1/jobs/{id}/apply/` | One-tap apply |
| POST | `/api/v1/jobs/{id}/withdraw/` | Withdraw application |
| GET | `/api/v1/jobs/my-applications/` | Doctor's applications |
| GET | `/api/v1/jobs/{id}/applications/` | Hospital — view applicants |
| PATCH | `/api/v1/jobs/applications/{id}/status/` | Update application status |

---

## 4. Module 3 — Doctor Availability Exchange

> Structured locum & part-time marketplace — doctors post availability, hospitals post urgent requirements, system matches & manages full shift lifecycle.

### 4.1 Doctor Availability

```
┌─────────────────────────────────────────────────────────────┐
│               DOCTOR AVAILABILITY POSTING                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Dr. Priya Mehta — Anesthesiologist                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Type:     LOCUM                                    │   │
│  │  From:     15 Aug 2025  →  30 Aug 2025              │   │
│  │  Location: Mumbai, Maharashtra  (50 km radius)      │   │
│  │  Min Pay:  ₹8,000 / shift                           │   │
│  │  Slots:    Mon 09:00–17:00  |  Wed 09:00–17:00      │   │
│  └─────────────────────────────────────────────────────┘   │
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
│  Apollo Hospital, Mumbai — ICU Department                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Specialty:   Anesthesiology                        │   │
│  │  Date:        18 Aug 2025                           │   │
│  │  Time:        08:00 – 20:00  (12 hr shift)          │   │
│  │  Doctors:     2 required                            │   │
│  │  Pay:         ₹12,000 / shift                       │   │
│  │  Urgency:     🔴 IMMEDIATE                          │   │
│  └─────────────────────────────────────────────────────┘   │
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
│  Hospital posts ShiftRequirement                           │
│           │                                                 │
│           ▼                                                 │
│  System filters DoctorAvailability where:                  │
│    • availability_type matches requirement type            │
│    • available_from ≤ requirement_date ≤ available_until   │
│    • preferred_location within preferred_radius_km         │
│    • minimum_compensation ≤ requirement compensation       │
│    • slot exists for requirement date & time               │
│           │                                                 │
│           ▼                                                 │
│  Matched doctors list returned to hospital                 │
│  Hospital sends ShiftRequest to selected doctors           │
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
| POST | `/api/v1/availability/` | Doctor posts availability |
| GET | `/api/v1/availability/me/` | List my availabilities |
| DELETE | `/api/v1/availability/{id}/` | Deactivate availability |
| GET | `/api/v1/availability/{id}/slots/` | List slots for an availability |
| POST | `/api/v1/shifts/requirements/` | Hospital posts shift requirement |
| GET | `/api/v1/shifts/requirements/` | List open shift requirements |
| GET | `/api/v1/shifts/requirements/mine/` | Hospital's own requirements |
| POST | `/api/v1/shifts/requirements/{id}/request/` | Doctor requests a shift |
| PATCH | `/api/v1/shifts/requests/{id}/respond/` | Doctor accepts / declines |
| PATCH | `/api/v1/shifts/requests/{id}/confirm/` | Hospital confirms shift |
| GET | `/api/v1/shifts/requests/mine/` | Doctor's shift requests |

---

## 5. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐     ┌─────────────────────┐                       │
│  │  Doctor Mobile App   │     │  Hospital CRM       │                       │
│  │  (Android Native)    │     │  (React Web)        │                       │
│  └──────────┬──────────┘     └──────────┬──────────┘                       │
│             │                            │                                  │
│             └──────────┬─────────────────┘                                  │
│                        │                                                    │
└────────────────────────┼────────────────────────────────────────────────────┘
                         │ HTTPS / REST API
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY / NGINX                                │
│                         (Load Balancer + SSL Termination)                  │
└─────────────────────────────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │                        FastAPI Layer                             │      │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │      │
│  │  │ Auth     │ │ Doctors  │ │ Network  │ │  Jobs    │           │      │
│  │  │ Router   │ │ Router   │ │ Router   │ │ Router   │           │      │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │      │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │      │
│  │  │ Avail-   │ │ Messages │ │ Notific- │ │ Admin    │           │      │
│  │  │ ability  │ │ Router   │ │ ations   │ │ Router   │           │      │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                                    │                                        │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │                      Django 5.0+ Core Layer                      │      │
│  │                                                                  │      │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │      │
│  │  │ Models   │ │ Admin    │ │ ORM      │ │ Celery  │           │      │
│  │  │ Layer    │ │ Interface│ │ Queries  │ │ Tasks   │           │      │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DATA & CACHE LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────┐    │
│  │   PostgreSQL    │    │    Redis        │    │   Celery + Redis    │    │
│  │   16+           │    │   7.2+          │    │   (Background Tasks)│    │
│  └─────────────────┘    └─────────────────┘    └─────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                     AWS S3 (File Storage)                       │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW DIAGRAM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DOCTOR REGISTRATION FLOW:                                                 │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐ │
│  │ Mobile  │──▶│ OTP     │──▶│ Profile  │──▶│ NMC      │──▶│ Verified  │ │
│  │ Number  │   │ Verify  │   │ Create   │   │ Verify   │   │ Profile   │ │
│  └─────────┘   └─────────┘   └──────────┘   └──────────┘   └───────────┘ │
│                                                                             │
│  JOB APPLICATION FLOW:                                                     │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐ │
│  │ Browse  │──▶│ Apply   │──▶│ Shortlist│──▶│ Interview│──▶│ Hired/    │ │
│  │ Jobs    │   │ One-Tap │   │          │   │          │   │ Rejected  │ │
│  └─────────┘   └─────────┘   └──────────┘   └──────────┘   └───────────┘ │
│                                                                             │
│  SHIFT REQUEST FLOW:                                                       │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐ │
│  │ Create  │──▶│ Match   │──▶│ Send     │──▶│ Accept/  │──▶│ Confirm/  │ │
│  │ Request │   │ Doctors │   │ Request  │   │ Decline  │   │ Complete  │ │
│  └─────────┘   └─────────┘   └──────────┘   └──────────┘   └───────────┘ │
│                                                                             │
│  HOSPITAL REGISTRATION FLOW:                                               │
│  ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐ │
│  │ Admin   │──▶│ OTP     │──▶│ Hospital │──▶│ Document │──▶│ Verified  │ │
│  │ Phone   │   │ Verify  │   │ Details  │   │ Upload   │   │ Hospital  │ │
│  └─────────┘   └─────────┘   └──────────┘   └──────────┘   └───────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Technology Stack

### 3.1 Core Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Backend Core** | Django | 5.0+ | ORM, Admin, Models, Auth |
| **API Layer** | FastAPI | 0.104+ | High-performance REST API |
| **Database** | PostgreSQL | 16+ | Primary database with advanced features |
| **Cache/Broker** | Redis | 7.2+ | Caching and Celery broker |
| **Task Queue** | Celery | 5.3+ | Background task processing |
| **API Docs** | FastAPI Swagger | - | Automatic OpenAPI documentation |
| **Validation** | Pydantic | 2.4+ | Data validation and serialization |

### 3.2 Frontend Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Mobile App** | Android Native | - | Doctor mobile application |
| **CRM Web** | React | 18+ | Hospital administration interface |
| **State Management** | Zustand/Redux | - | Client state management |
| **API Client** | React Query | - | Data fetching and caching |

### 3.3 DevOps & Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Containerization** | Docker | Container runtime |
| **Orchestration** | Docker Compose | Local development |
| **Hosting** | AWS EC2 / ECS | Production hosting |
| **CI/CD** | GitHub Actions | Automated deployment |
| **Monitoring** | Sentry / Prometheus | Error tracking |
| **Logging** | ELK Stack | Log aggregation |

### 3.4 PostgreSQL Extensions

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

## 7. Database Design

### 4.1 Complete Database Schema

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

## 8. API Architecture (FastAPI)

### 5.1 FastAPI Integration with Django

```python
# fastapi_app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
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
app.include_router(shift_router)

# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
async def root():
    return {
        "name": "DocConnect API",
        "version": "1.0.0",
        "description": "Verified Professional Network for Doctors",
        "documentation": "/api/docs",
        "redoc": "/api/redoc",
        "openapi": "/api/openapi.json"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
```

### 5.2 Running FastAPI with Django

```python
# run.py - Combined server runner
import uvicorn
import os
import sys

if __name__ == "__main__":
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docconnect_backend.settings')
    
    # Run FastAPI with uvicorn
    uvicorn.run(
        "fastapi_app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

---

## 9. Project Structure

```
docconnect/
├── manage.py
├── run.py                     # FastAPI + Django runner
├── requirements.txt
├── .env
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.fastapi
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
│   ├── wsgi.py
│   └── asgi.py
│
├── fastapi_app/               # FastAPI Application
│   ├── __init__.py
│   ├── main.py                # Main FastAPI app
│   ├── dependencies.py        # Dependency injections
│   ├── schemas.py             # Pydantic models
│   ├── routers/               # API routers
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── doctors.py
│   │   ├── jobs.py
│   │   ├── availability.py
│   │   ├── shifts.py
│   │   └── messaging.py
│   └── middleware/            # FastAPI middleware
│       ├── __init__.py
│       ├── auth.py
│       └── logging.py
│
├── apps/                      # Django Apps
│   ├── __init__.py
│   ├── accounts/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   └── managers.py
│   ├── doctors/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   └── managers.py
│   ├── hospitals/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   └── models.py      # Hospital, HospitalBranch, HospitalDepartment, HospitalUser
│   ├── jobs/
│   ├── availability/
│   ├── shifts/
│   ├── messaging/
│   ├── notifications/
│   └── core/
│
├── tests/                     # Tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_doctors.py
│   ├── test_jobs.py
│   └── test_availability.py
│
├── scripts/                   # Utility scripts
│   ├── seed_data.py
│   ├── create_admin.py
│   └── update_search_vectors.py
│
├── nginx/                     # Nginx configuration
│   ├── nginx.conf
│   └── ssl/
│
└── docs/                      # Documentation
    ├── api/
    ├── architecture/
    └── deployment/
```

---

## 10. Development Setup

### 7.1 Prerequisites

- Python 3.13+ (3.14 also works — tested)
- PostgreSQL 16+
- Redis 7.2+

### 7.2 Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/yourusername/docconnect.git
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

### 7.3 All URLs

| URL | Description |
|-----|-------------|
| http://localhost:8000/ | API root |
| http://localhost:8000/api/docs | Swagger UI (interactive API docs) |
| http://localhost:8000/api/redoc | ReDoc API docs |
| http://localhost:8000/api/openapi.json | OpenAPI schema |
| http://localhost:8000/health | Health check |
| http://localhost:8000/admin/ | Django Admin panel |

### 7.4 Super Admin Credentials

| Field | Value |
|-------|-------|
| Phone | `9999999999` |
| Password | `admin123` |
| User Type | `ADMIN` |

> **Note:** Change password immediately in production via Django Admin → Users.

### 7.5 Python 3.14 Compatibility Notes

If you are on Python 3.14 (Windows), the following pinned versions are required in `requirements.txt` — they ship pre-built wheels for 3.14:

```
pydantic[email]==2.13.4
pydantic-core==2.46.4
psycopg[binary]==3.3.4
fastapi==0.115.12
uvicorn[standard]==0.34.3
```

### 7.3 Docker Setup

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

## 11. Deployment

### 8.1 Environment Variables

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

### 8.2 Production Deployment

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

## 12. API Documentation

### 9.1 Access Swagger UI

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/openapi.json`

### 9.2 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Auth** | | |
| POST | `/api/v1/auth/send-otp/` | Send OTP to phone |
| POST | `/api/v1/auth/verify-otp/` | Verify OTP and login |
| POST | `/api/v1/auth/refresh/` | Refresh JWT token |
| **Doctors** | | |
| POST | `/api/v1/doctors/profile/` | Create doctor profile |
| GET | `/api/v1/doctors/profile/me/` | Get my profile |
| PUT | `/api/v1/doctors/profile/me/` | Update my profile |
| GET | `/api/v1/doctors/search/` | Search doctors |
| **Jobs** | | |
| POST | `/api/v1/jobs/` | Create job posting |
| GET | `/api/v1/jobs/` | List jobs |
| GET | `/api/v1/jobs/{id}/` | Get job details |
| POST | `/api/v1/jobs/{id}/apply/` | Apply to job |
| **Hospitals** | | |
| POST | `/api/v1/hospitals/register/` | Register new hospital |
| GET | `/api/v1/hospitals/me/` | Get my hospital profile |
| POST | `/api/v1/hospitals/me/branches/` | Add hospital branch |
| POST | `/api/v1/hospitals/me/departments/` | Add department |
| POST | `/api/v1/hospitals/me/invite-user/` | Invite HR/Recruiter |
| POST | `/api/v1/hospitals/me/upload-logo/` | Upload hospital logo |
| **Availability** | | |
| POST | `/api/v1/availability/` | Create availability |
| GET | `/api/v1/availability/me/` | Get my availability |
| PUT | `/api/v1/availability/me/` | Update availability |
| **Shifts** | | |
| POST | `/api/v1/shifts/requirements/` | Create shift requirement |
| GET | `/api/v1/shifts/requirements/` | List shift requirements |
| POST | `/api/v1/shifts/requests/` | Send shift request |
| GET | `/api/v1/shifts/requests/` | List shift requests |

---

## 13. Security

### 10.1 Authentication Flow

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

### 10.2 Security Features

```python
# Security headers middleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    HTTPSRedirectMiddleware,
    redirect_schemes=["http"]
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.docconnect.com", "*.docconnect.com"]
)

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/auth/send-otp/")
@limiter.limit("5/minute")
async def send_otp(request: OTPRequest):
    pass

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://docconnect.com", "https://www.docconnect.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID"],
    max_age=3600
)
```

### 10.3 Data Encryption

```python
# core/encryption.py
from cryptography.fernet import Fernet
import base64
import hashlib

class DataEncryption:
    def __init__(self, secret_key: str):
        key = hashlib.sha256(secret_key.encode()).digest()
        self.cipher = Fernet(base64.urlsafe_b64encode(key))
    
    def encrypt(self, data: str) -> str:
        if not data:
            return None
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data:
            return None
        encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()
```

---

## 14. Testing

### 11.1 Running Tests

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

### 11.2 Test Example

```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from fastapi_app.main import app

client = TestClient(app)

def test_send_otp():
    response = client.post(
        "/api/v1/auth/send-otp/",
        json={"phone": "9876543210", "purpose": "LOGIN"}
    )
    assert response.status_code == 200
    assert response.json()["success"] == True

def test_verify_otp_invalid():
    response = client.post(
        "/api/v1/auth/verify-otp/",
        json={"phone": "9876543210", "otp": "000000"}
    )
    assert response.status_code == 400
    assert "Invalid OTP" in response.json()["detail"]
```

---

## 15. Troubleshooting

### 12.1 Common Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| `django.db.utils.OperationalError` | PostgreSQL not running | `sudo service postgresql start` |
| `ModuleNotFoundError: No module named 'django'` | Virtualenv not activated | `source venv/bin/activate` |
| FastAPI returns 401 on all requests | JWT secret mismatch | Ensure `JWT_SECRET_KEY` matches in `.env` |
| Celery tasks not executing | Redis not running | `redis-server` or `docker-compose up redis` |
| `postgis` extension missing | PostGIS not installed | `sudo apt install postgresql-16-postgis-3` |
| OTP SMS not delivered | Invalid `SMS_API_KEY` | Check provider dashboard for key validity |

### 12.2 Logs

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

## 16. Roadmap

### Phase 1 — MVP (Current)
- [x] OTP-based authentication
- [x] Doctor profile with NMC verification
- [x] Job posting & one-tap apply
- [x] Doctor availability & shift marketplace
- [x] Basic messaging

### Phase 2 — Q3 2026
- [ ] Doctor connections (send / accept / withdraw)
- [ ] Feed & post system (clinical cases, articles, updates)
- [ ] Specialty communities & group discussions
- [ ] Hospital verification via document OCR
- [ ] AI-powered job matching score (specialty + experience + location + qualification)
- [ ] Push notifications via FCM
- [ ] CME credit tracking
- [ ] iOS app support

### Phase 3 — Q4 2026
- [ ] Peer endorsements & skill recommendations
- [ ] Second opinion & case referral network
- [ ] Hospital analytics dashboard (applications, hires, shift fill rate)
- [ ] Telemedicine / video consultation scheduling
- [ ] Multi-language support (Hindi, Tamil, Telugu)
- [ ] AI-powered doctor matching for shift requirements

---

## 17. Contributing

### 14.1 Development Guidelines

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

### 14.2 Pull Request Process

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
- **GitHub**: https://github.com/docconnect/docconnect

---

**DocConnect — Building Trusted Doctor Professional Network**

---

*Last updated: August 2026 | Maintained by Pavan Kumar Dubey*