# DocConnect — Mobile Integration Guide (Android & iOS)

> **Base URL:** `http://3.111.58.158/api/v1`
> **Swagger UI:** `http://3.111.58.158/api/docs`
> **Format:** JSON | **Auth:** Bearer Token

---

## IMPORTANT — Headers for Every Request

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

For file uploads use:
```
Content-Type: multipart/form-data
```

---

## PART 1 — DOCTOR APP SCREENS & API MAPPING

---

### SCREEN 1: Splash / App Launch

**What to do:** Check if user is already logged in (token stored locally).

- If token exists → call token refresh → go to Home
- If no token → go to Login/Register screen

```
POST /auth/refresh/
Body: { "refresh_token": "<stored_refresh_token>" }
→ Save new access_token
```

---

### SCREEN 2: Register Screen

**User fills:** Name, Phone, Password, User Type

```
POST /auth/register/
Body:
{
  "first_name": "Arjun",
  "last_name": "Sharma",
  "phone": "9876543210",
  "password": "securepass123",
  "user_type": "DOCTOR"
}

Response → save access_token + refresh_token locally
```

> After register → go to Profile Setup (Screen 4)

---

### SCREEN 3: Login Screen

**Option A — Phone + Password:**
```
POST /auth/login/
Body:
{
  "phone": "9876543210",
  "password": "securepass123",
  "user_type": "DOCTOR",
  "device_id": "<device_uuid>"
}
Response → save access_token + refresh_token
```

**Option B — OTP Login:**
```
Step 1: POST /auth/send-otp/
Body: { "phone": "9876543210", "purpose": "LOGIN" }

Step 2: POST /auth/verify-otp/
Body:
{
  "phone": "9876543210",
  "otp": "123456",
  "purpose": "LOGIN",
  "user_type": "DOCTOR"
}
Response → save access_token + refresh_token
```

> After login → Register device for push notifications (Screen 3a), then go to Home

---

### SCREEN 3a: Register Device (call immediately after login)

```
POST /devices/
Body:
{
  "token": "<FCM_token_android_or_APNS_token_ios>",
  "platform": "ANDROID",   ← or "IOS"
  "device_id": "<device_uuid>",
  "app_version": "1.0.0"
}
```

> Call this silently in background after every login.

---

### SCREEN 4: Doctor Profile Setup (Onboarding — First Time Only)

**Step 1 — Load master data first (for dropdowns):**
```
GET /masters/specialties/       → specialty dropdown
GET /masters/qualifications/    → qualification dropdown
```

**Step 2 — Create profile:**
```
POST /doctors/profile/
Body:
{
  "first_name": "Arjun",
  "last_name": "Sharma",
  "headline": "Cardiologist · AIIMS Delhi · 12 yrs",
  "about": "Senior cardiologist...",
  "primary_specialization_id": "<uuid from specialties>",
  "professional_location": {
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001"
  },
  "experience_years": 12.0
}
```

**Step 3 — Upload profile photo (optional):**
```
POST /doctors/profile/me/photo/
Body: multipart/form-data → file: <image>
```

**Step 4 — Add NMC Registration:**
```
POST /doctors/profile/me/registrations/
Body:
{
  "council_id": "<uuid>",
  "registration_number": "MH-12345",
  "registration_year": 2010,
  "is_primary": true
}
```

**Step 5 — Submit for Verification:**
```
POST /doctors/profile/me/verification/submit/
→ Status becomes PENDING
```

---

### SCREEN 5: Home Screen

---

#### RULE #1 — Home screen ke liye 2 APIs hain, dono PARALLEL call karo

```
┌─────────────────────────────────────────────────────┐
│  Screen load hote hi — DONO SAATH call karo         │
│                                                     │
│  CALL A:  GET /feed/home/    ← stats, jobs, doctors │
│  CALL B:  GET /feed/?page=1  ← actual post feed     │
│                                                     │
│  Ek ka dusre se koi relation nahi.                  │
│  Dono ka wait mat karo — parallel bhejo.            │
└─────────────────────────────────────────────────────┘
```

---

#### CALL A — `GET /feed/home/` ka poora response

```json
{
  "stats": {
    "doctors": 1500,
    "hospitals": 200,
    "jobs": 350
  },

  "urgent_jobs": [
    {
      "id": "uuid-job-1",
      "title": "Emergency Anesthesiologist",
      "hospital_name": "Apollo Hospital",
      "hospital_logo": null,
      "job_type": "LOCUM",
      "job_type_display": "Locum",
      "location": { "city": "Mumbai" },
      "salary_min": 15000,
      "salary_max": null,
      "salary_visibility": "PUBLIC",
      "experience_min_years": 3.0,
      "is_urgent": true,
      "posted_at": "Aug 15"
    }
  ],

  "suggested_doctors": [
    {
      "id": "uuid-doc-1",
      "full_name": "Dr. Priya Mehta",
      "headline": "Neurologist · 8 yrs",
      "photo": null,
      "initials": "PM",
      "color": "#057642",
      "location": { "city": "Delhi" },
      "experience_years": 8.0,
      "verification_status": "VERIFIED",
      "connection_status": null,
      "connection_id": null,
      "connection_direction": null
    }
  ],

  "unread_messages": 3,
  "unread_notifications": 7,
  "pending_connections": 2
}
```

---

#### CALL B — `GET /feed/?page=1` ka poora response

```json
{
  "posts": [
    {
      "id": "uuid-post-1",
      "author": "Dr. Arjun Sharma",
      "author_id": "uuid",
      "headline": "Cardiologist · 12 yrs",
      "initials": "AS",
      "color": "#0a66c2",
      "photo": null,
      "post_type": "UPDATE",
      "post_type_display": "Update",
      "content": "Excited to share my research...",
      "image": null,
      "like_count": 24,
      "comment_count": 5,
      "liked": false,
      "is_mine": false,
      "pii_flagged": false,
      "created_at": "Aug 15"
    }
  ],
  "page": 1,
  "page_size": 10,
  "has_more": true
}
```

---

#### Screen Layout — kaunsa data kahan jaata hai

```
┌──────────────────────────────────────────────────────┐
│  TOP BAR                                             │
│  DocConnect Logo    🔔 7    💬 3                     │
│                     ▲           ▲                    │
│              unread_notifications  unread_messages   │
│              (home API se)         (home API se)     │
├──────────────────────────────────────────────────────┤
│  STATS BANNER                                        │
│  1,500 Doctors · 200 Hospitals · 350 Jobs            │
│  ▲              ▲                ▲                   │
│  stats.doctors  stats.hospitals  stats.jobs          │
│  (home API se)                                       │
├──────────────────────────────────────────────────────┤
│  🔴 URGENT OPENINGS              [See All →]         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │Apollo Hosp │  │Fortis Hosp │  │Max Hosp    │     │
│  │Anesthesiol.│  │Cardiologis.│  │Neurologist │     │
│  │Locum       │  │Full Time   │  │Locum       │     │
│  │₹15,000     │  │₹12,000     │  │₹10,000     │     │
│  │Aug 15      │  │Aug 14      │  │Aug 13      │     │
│  └────────────┘  └────────────┘  └────────────┘     │
│  ▲ urgent_jobs[0]  ▲ [1]           ▲ [2]            │
│  (home API se — max 3 cards)                         │
├──────────────────────────────────────────────────────┤
│  👥 PEOPLE YOU MAY KNOW          [See All →]         │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │  PM    │ │  AS    │ │  RK    │ │  SJ    │        │
│  │Dr.Priya│ │Dr.Arjun│ │Dr.Rahul│ │Dr.Sona │        │
│  │Neurolog│ │Cardiol.│ │Pediatr.│ │Orthoped│        │
│  │[Connect│ │[Connect│ │[Connect│ │[Connect│        │
│  └────────┘ └────────┘ └────────┘ └────────┘        │
│  ▲ suggested_doctors[0..3] (home API se — max 4)     │
├──────────────────────────────────────────────────────┤
│  📰 FEED                                             │
│  ┌──────────────────────────────────────────────┐   │
│  │ [AS] Dr. Arjun Sharma · Cardiologist · Aug15 │   │
│  │ Excited to share my research on...           │   │
│  │ 👍 24  💬 5  [Like] [Comment] [Share]        │   │
│  └──────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────┐   │
│  │ [PM] Dr. Priya Mehta · Neurologist · Aug 14  │   │
│  │ New case study published...                  │   │
│  │ 👍 12  💬 3  [Like] [Comment] [Share]        │   │
│  └──────────────────────────────────────────────┘   │
│  ▲ posts[] (feed API se — GET /feed/?page=1)         │
│  (neeche scroll karo → page=2, page=3...)            │
├──────────────────────────────────────────────────────┤
│  BOTTOM TAB BAR                                      │
│  🏠Home  💼Jobs  👥Network🔴2  💬Chat🔴3  🔔Bell🔴7 │
│                       ▲              ▲         ▲    │
│               pending_connections  unread_  unread_ │
│               (home API se)        messages notifs  │
└──────────────────────────────────────────────────────┘
```

---

#### User Actions — kaunsa tap kaunsi API call karega

**Urgent Job card tap:**
```
Job card tap    →  GET /jobs/{urgent_jobs[i].id}/
Apply button    →  POST /jobs/{id}/apply/
"See All" tap   →  GET /jobs/?is_urgent=true
```

**Suggested Doctor card — Connect button logic:**
```
connection_status == null
  → "Connect" button dikhao
  → tap karo → POST /network/connections/request/
                body: { "receiver_id": "suggested_doctors[i].id" }

connection_status == "PENDING" AND connection_direction == "sent"
  → "Pending" button dikhao (disabled, grey)
  → koi API call nahi

connection_status == "PENDING" AND connection_direction == "received"
  → "Accept" button dikhao
  → tap karo → POST /network/connections/{connection_id}/accept/

connection_status == "ACCEPTED"
  → "Message" button dikhao
  → tap karo → POST /messages/conversations/
                body: { "participant_user_id": "doctor ka user_id" }

Doctor name/photo tap
  → GET /doctors/profile/{suggested_doctors[i].id}/

"See All" tap
  → GET /doctors/search/
```

**Feed post actions:**
```
Like button tap    →  POST /feed/posts/{post.id}/like/
                       response: { liked: true/false, count: 25 }

Comment tap        →  GET /feed/posts/{post.id}/comments/

Comment likhna     →  POST /feed/posts/{post.id}/comments/
                       body (form-data): content="Great post!"

Author name tap    →  GET /doctors/profile/{post.author_id}/

is_mine == true    →  3-dot menu dikhao (Edit / Delete)
  Edit             →  PATCH /feed/posts/{post.id}/
  Delete           →  DELETE /feed/posts/{post.id}/
```

**Feed infinite scroll:**
```
User scrolls to bottom
  has_more == true  →  GET /feed/?page=2
                    →  GET /feed/?page=3
                    →  jab tak has_more == false
  has_more == false →  "No more posts" dikhao
```

---

#### Data source quick reference

| Screen element | Kahan se aata hai | Max items |
|----------------|-------------------|-----------|
| Top bar badges (🔔💬) | `GET /feed/home/` → `unread_notifications`, `unread_messages` | — |
| Network tab badge (👥) | `GET /feed/home/` → `pending_connections` | — |
| Stats banner | `GET /feed/home/` → `stats{}` | — |
| Urgent job cards | `GET /feed/home/` → `urgent_jobs[]` | 3 |
| People you may know | `GET /feed/home/` → `suggested_doctors[]` | 4 |
| Feed posts | `GET /feed/?page=1` → `posts[]` | 10 per page |
| Sab urgent jobs | `GET /jobs/?is_urgent=true` | paginated |
| Sab doctors | `GET /doctors/search/` | paginated |

---

### SCREEN 6: Feed Screen

**Load feed posts:**
```
GET /feed/?page=1&page_size=10
→ Returns posts[], has_more (for infinite scroll)
```

**Infinite scroll — load next page:**
```
GET /feed/?page=2&page_size=10
```

**Like/Unlike a post (toggle):**
```
POST /feed/posts/{post_id}/like/
→ Returns { liked: true/false, count: 25 }
```

**View comments:**
```
GET /feed/posts/{post_id}/comments/
→ Returns comments with nested replies[]
```

**Add comment:**
```
POST /feed/posts/{post_id}/comments/
Body: multipart/form-data → content: "Great post!"
```

**Reply to comment:**
```
POST /feed/comments/{comment_id}/reply/
Body: multipart/form-data → content: "Thanks!"
```

**Create new post:**
```
POST /feed/posts/
Body: multipart/form-data
Fields:
  content: "Post text here"
  post_type: "UPDATE"   ← UPDATE / CASE / ARTICLE / PHOTO
  image: <file>         ← optional
  is_anonymous: false   ← for CASE type only
  patient_privacy_confirmed: true  ← REQUIRED for CASE type
```

---

### SCREEN 7: My Profile Screen

**Load my profile:**
```
GET /doctors/profile/me/
```

**Load qualifications, experiences, affiliations (call in parallel):**
```
GET /doctors/profile/me/qualifications/
GET /doctors/profile/me/experiences/
GET /doctors/profile/me/affiliations/
GET /doctors/profile/me/registrations/
```

**Check verification status:**
```
GET /doctors/profile/me/verification/
→ verification_status: UNVERIFIED / PENDING / VERIFIED / REJECTED
```

> If REJECTED → show resubmit button → `POST /doctors/profile/me/verification/resubmit/`

**Edit profile:**
```
PATCH /doctors/profile/me/
Body: { "headline": "...", "about": "...", "experience_years": 13 }
```

**Toggle "Open to Opportunities":**
```
PUT /doctors/profile/me/status/
Body: { "open_to_opportunities": true, "career_visibility": "VERIFIED_HOSPITALS" }
```

---

### SCREEN 8: View Another Doctor's Profile

```
GET /doctors/profile/{doctor_id}/
→ 403 if profile is private/connections-only
```

**Send connection request from profile:**
```
POST /network/connections/request/
Body: { "receiver_id": "<doctor_id>" }
```

---

### SCREEN 9: Search Screen

**Search doctors:**
```
GET /doctors/search/?search=arjun&specialty=<uuid>&city=Mumbai&page=1
```

**Universal search (all entities):**
```
GET /search/universal/?q=cardiology
→ Returns doctors[], hospitals[], jobs[], communities[]
```

**Search jobs:**
```
GET /search/jobs/?search=cardiologist&city=Mumbai
```

---

### SCREEN 10: Jobs Screen

**Browse all jobs:**
```
GET /jobs/?page=1&page_size=20
```

**Filter jobs:**
```
GET /jobs/?specialty=<uuid>&city=Mumbai&job_type=FULL_TIME&is_urgent=true
```

**View job detail:**
```
GET /jobs/{job_id}/
```

**One-tap apply:**
```
POST /jobs/{job_id}/apply/
→ Returns { application_id, status: "APPLIED" }
```

**Save job for later:**
```
POST /jobs/{job_id}/save/
```

**View saved jobs:**
```
GET /doctors/me/saved-jobs/
```

**View my applications:**
```
GET /jobs/my-applications/?status=APPLIED
```

**Withdraw application:**
```
POST /jobs/{job_id}/withdraw/
```

**AI recommended jobs:**
```
GET /doctors/me/job-recommendations/
```

---

### SCREEN 11: Network / Connections Screen

**Load connections (tabs):**
```
GET /network/connections/?type=accepted    ← My Connections tab
GET /network/connections/?type=received    ← Pending Requests tab
GET /network/connections/?type=sent        ← Sent Requests tab
```

**Accept request:**
```
POST /network/connections/{connection_id}/accept/
```

**Reject request:**
```
POST /network/connections/{connection_id}/reject/
```

**Withdraw sent request:**
```
DELETE /network/connections/{connection_id}/
```

**Follow a hospital:**
```
POST /network/follow/{hospital_user_id}/
```

**Block a user:**
```
POST /network/block/{user_id}/
```

---

### SCREEN 12: Messages Screen

**List all conversations:**
```
GET /messages/conversations/
```

**Open a conversation / load messages:**
```
GET /messages/conversations/{conversation_id}/messages/?page=1&page_size=50
```

**Send message:**
```
POST /messages/conversations/{conversation_id}/messages/
Body: { "content": "Hello doctor", "message_type": "TEXT" }
```

**Mark as read (call when user opens conversation):**
```
POST /messages/conversations/{conversation_id}/read/
```

**Start new conversation with a doctor:**
```
POST /messages/conversations/
Body: { "participant_user_id": "<doctor_user_id>" }
→ Returns conversation_id (existing: true if already exists)
```

---

### SCREEN 13: Notifications Screen

**Load notifications:**
```
GET /notifications/?page=1
```

**Get unread count (for badge — call on app resume):**
```
GET /notifications/unread-count/
```

**Mark one as read:**
```
PATCH /notifications/{notification_id}/read/
```

**Mark all as read:**
```
POST /notifications/read-all/
```

---

### SCREEN 14: Availability Screen (Locum/Visiting)

**Post my availability:**
```
POST /availability/
Body:
{
  "availability_type": "LOCUM",
  "available_from": "2025-08-15",
  "available_until": "2025-08-30",
  "preferred_location": { "city": "Mumbai", "state": "Maharashtra" },
  "preferred_radius_km": 50,
  "minimum_compensation": 8000,
  "currency": "INR",
  "slots": [
    { "slot_date": "2025-08-15", "start_time": "09:00:00", "end_time": "17:00:00" }
  ]
}
```

**View my availabilities:**
```
GET /availability/me/
```

**Browse urgent shift requirements:**
```
GET /shifts/requirements/?urgency=IMMEDIATE&city=Mumbai&specialty=<uuid>
```

**Request a shift:**
```
POST /shifts/requirements/{requirement_id}/request/
```

**My shift requests:**
```
GET /shifts/requests/mine/
```

**Accept/Decline a shift request from hospital:**
```
PATCH /shifts/requests/{request_id}/respond/
Body: { "accept": true }   ← or false to decline
```

---

### SCREEN 15: Communities Screen

**List communities:**
```
GET /communities/?page=1
```

**Join a community:**
```
POST /communities/{community_id}/join/
```

**View community posts:**
```
GET /communities/{community_id}/posts/?page=1
```

**Post in community:**
```
POST /communities/{community_id}/posts/
Body: multipart/form-data → content, post_type, image (optional)
```

---

### SCREEN 16: Settings Screen

**Privacy settings:**
```
GET /doctors/profile/me/privacy/
PUT /doctors/profile/me/privacy/
Body: { "profile_visibility": "DOCTORS_ONLY", "career_visibility": "VERIFIED_HOSPITALS" }
```

**Notification preferences:**
```
GET /notification-preferences/
PUT /notification-preferences/
Body: { "connection_request": { "push": true, "email": false } }
```

**Change password:**
```
POST /auth/password/change/
Body: { "old_password": "...", "new_password": "..." }
```

**Active sessions:**
```
GET /auth/sessions/
DELETE /auth/sessions/{session_id}/
POST /auth/sessions/revoke-all/
```

**Logout:**
```
POST /auth/logout/
→ Then clear stored tokens locally
```

---

### SCREEN 17: Forgot Password

```
Step 1: POST /auth/password/forgot/
Body: { "phone": "9876543210" }

Step 2: POST /auth/password/reset/
Body: { "phone": "9876543210", "otp": "123456", "new_password": "newpass123" }
```

---

### SCREEN 18: Support / Help

**Raise ticket:**
```
POST /support/tickets/
Body: { "subject": "...", "description": "...", "category": "VERIFICATION" }
```

**View my tickets:**
```
GET /support/tickets/
```

**Reply to ticket:**
```
POST /support/tickets/{ticket_id}/messages/
Body: { "message": "..." }
```

---

### SCREEN 19: Report Content

**Report a post/profile/job:**
```
POST /reports/
Body:
{
  "target_type": "POST",
  "target_id": "<uuid>",
  "reason": "SPAM",
  "description": "This is spam",
  "severity": "MEDIUM"
}
```

---

## PART 2 — HOSPITAL APP SCREENS & API MAPPING

---

### SCREEN H1: Hospital Register & Login

Same as Doctor — use `user_type: "HOSPITAL_ADMIN"` in register/login.

After login → Register hospital:
```
POST /hospitals/register/
Body:
{
  "name": "Apollo Hospital",
  "type": "HOSPITAL",
  "location": { "city": "Mumbai", "state": "Maharashtra", "pincode": "400001" },
  "bed_count": 500,
  "hospital_phone": "9876543210",
  "hospital_email": "info@apollo.com"
}
```

Submit for verification:
```
POST /hospitals/me/verification/submit/
```

---

### SCREEN H2: Hospital Dashboard

```
GET /analytics/hospital/
→ total_jobs_active, total_applications, total_hired, total_shifts_filled

GET /feed/home/
→ unread_messages, unread_notifications
```

---

### SCREEN H3: Post a Job

**Load dropdowns first:**
```
GET /masters/specialties/
GET /masters/qualifications/
GET /masters/job-types/
GET /masters/shift-types/
GET /hospitals/me/departments/
```

**Create job:**
```
POST /jobs/
Body:
{
  "title": "Senior Cardiologist",
  "specialty_id": "<uuid>",
  "qualification_ids": ["<uuid>"],
  "description": "...",
  "location": { "city": "Mumbai", "state": "Maharashtra" },
  "salary_min": 150000,
  "salary_max": 250000,
  "salary_visibility": "PUBLIC",
  "job_type": "FULL_TIME",
  "experience_min_years": 5,
  "shift_type": "DAY",
  "positions": 2,
  "is_urgent": false,
  "closing_date": "2025-12-31T00:00:00Z"
}
```

---

### SCREEN H4: Manage Jobs

**List my jobs:**
```
GET /jobs/?page=1
```

**Close a job:**
```
POST /jobs/{job_id}/close/
```

**View applicants for a job:**
```
GET /jobs/{job_id}/applications/?status=APPLIED
```

---

### SCREEN H5: Application Pipeline (Recruitment CRM)

**Move application through pipeline:**
```
PATCH /jobs/applications/{application_id}/status/
Body: { "status": "SHORTLISTED", "notes": "Strong candidate" }

Status flow: APPLIED → PROFILE_VIEWED → SHORTLISTED → INTERVIEW → OFFERED → HIRED
```

**Schedule interview:**
```
POST /applications/{application_id}/interview/
Body: { "scheduled_at": "2025-08-20T10:00:00Z", "mode": "VIDEO", "notes": "Tech round" }
```

**Update interview outcome:**
```
PATCH /applications/{application_id}/interview/{interview_id}/
Params: outcome=PASS
```

**Send offer:**
```
POST /applications/{application_id}/offer/
Body: { "salary": "200000", "joining_date": "2025-09-01" }
```

**Add internal HR note:**
```
POST /applications/{application_id}/notes/
Body: { "note": "Good communication skills" }
```

---

### SCREEN H6: Candidate Discovery

**Search doctors:**
```
GET /hospitals/me/candidates/?specialty=<uuid>&city=Mumbai&verified_only=true&experience_min=5
```

**Invite doctor to apply:**
```
POST /applications/{application_id}/invite/
Body: { "doctor_id": "<uuid>", "job_id": "<uuid>" }
```

**View AI matched doctors for a job:**
```
GET /jobs/{job_id}/matches/
```

---

### SCREEN H7: Urgent Shift Requirements

**Post urgent requirement:**
```
POST /shifts/requirements/
Body:
{
  "specialty_id": "<uuid>",
  "requirement_date": "2025-08-18",
  "start_time": "08:00:00",
  "end_time": "20:00:00",
  "location": { "city": "Mumbai", "state": "Maharashtra" },
  "compensation": 12000,
  "currency": "INR",
  "doctors_required": 2,
  "urgency": "URGENT",
  "notes": "ICU coverage needed"
}
```

**Get matched doctors for requirement:**
```
GET /shifts/requirements/{requirement_id}/matched-doctors/
```

**Send shift request to a doctor:**
```
POST /shifts/requirements/{requirement_id}/request/
```

**Confirm after doctor accepts:**
```
PATCH /shifts/requests/{request_id}/confirm/
```

**Mark shift completed:**
```
PATCH /shifts/requests/{request_id}/complete/
```

---

### SCREEN H8: Hospital Profile Management

```
GET /hospitals/me/
PATCH /hospitals/me/
POST /hospitals/me/upload-logo/   ← multipart/form-data, file: <image>
```

**Branches:**
```
POST /hospitals/me/branches/
GET /hospitals/me/branches/
PATCH /hospitals/me/branches/{id}/
```

**Departments:**
```
POST /hospitals/me/departments/
GET /hospitals/me/departments/
```

**Add HR/Recruiter:**
```
POST /hospitals/me/invite-user/
Body: { "phone": "9876543210", "role": "HR", "designation": "HR Manager" }
```

---

## PART 3 — TOKEN MANAGEMENT (Critical for Mobile)

### Token Storage
- Store `access_token` and `refresh_token` in secure storage (Keychain on iOS, EncryptedSharedPreferences on Android)

### Token Refresh Logic
```
Every API call:
  → If response is 401 Unauthorized:
      → POST /auth/refresh/ with refresh_token
      → If refresh succeeds → retry original request with new access_token
      → If refresh fails (401) → clear tokens → redirect to Login screen
```

### Token Expiry (approximate)
- `access_token`: short-lived (15–60 min)
- `refresh_token`: long-lived (7–30 days)

---

## PART 4 — PUSH NOTIFICATIONS

### Android (FCM) / iOS (APNs)

1. Get device token from FCM/APNs after app launch
2. Call `POST /devices/` with the token after every login
3. On logout call `DELETE /devices/{device_id}/` to stop notifications

### Notification Types to Handle
| type | Navigate to |
|------|-------------|
| `CONNECTION_REQUEST` | Network screen → Pending tab |
| `CONNECTION_ACCEPTED` | That doctor's profile |
| `JOB_APPLICATION` | Application detail (hospital) |
| `APPLICATION_STATUS_CHANGED` | My Applications screen (doctor) |
| `SHIFT_REQUEST` | Shift Requests screen |
| `NEW_MESSAGE` | Messages → that conversation |
| `VERIFICATION_APPROVED` | My Profile screen |
| `VERIFICATION_REJECTED` | My Profile → Verification section |

---

## PART 5 — FILE UPLOADS

### Upload any file first, then use the returned `id`:
```
POST /files/upload/
Body: multipart/form-data
  file: <file>
  purpose: "CV"   ← PROFILE_PHOTO / CV / CREDENTIAL / REPORT_EVIDENCE

Response: { "id": "uuid", "url": "https://..." }
```

### Get signed URL to display a file:
```
GET /files/{file_id}/signed-url/
→ Returns { url: "https://s3...", expires_in: 3600 }
```

> Always use signed URL to display images/documents. Never store the S3 URL directly.

---

## PART 6 — ERROR HANDLING

| HTTP Code | What happened | What to do |
|-----------|--------------|------------|
| 400 | Validation error | Show `detail` message to user |
| 401 | Token expired | Refresh token → retry |
| 403 | Wrong role/permission | Show "Access denied" |
| 404 | Resource not found | Show "Not found" |
| 409 | Conflict (duplicate/overlap) | Show conflict message |
| 429 | Rate limited | Wait and retry after delay |
| 500 | Server error | Show generic error, log it |

**Error response format always:**
```json
{ "detail": "Error message here" }
```

---

## PART 7 — PAGINATION

All list APIs support:
```
?page=1&page_size=20
```

Response always includes:
```json
{ "total": 100, "page": 1, "page_size": 20, "results": [...] }
```

For infinite scroll: keep loading next page until `results` is empty or `has_more` is false.

---

## PART 8 — COMPLETE DOCTOR ONBOARDING FLOW (Step by Step)

```
1. POST /auth/register/                              → get tokens
2. POST /devices/                                    → register push token
3. GET  /masters/specialties/                        → load dropdown
4. GET  /masters/qualifications/                     → load dropdown
5. POST /doctors/profile/                            → create profile
6. POST /doctors/profile/me/photo/                   → upload photo (optional)
7. POST /doctors/profile/me/qualifications/          → add MBBS/MD
8. POST /doctors/profile/me/experiences/             → add work history
9. POST /doctors/profile/me/registrations/           → add NMC number
10. POST /doctors/profile/me/verification/submit/    → submit for verification
11. GET  /feed/home/                                 → load home screen
```

---

## PART 9 — COMPLETE HOSPITAL ONBOARDING FLOW

```
1. POST /auth/register/                              → user_type: HOSPITAL_ADMIN
2. POST /devices/                                    → register push token
3. POST /hospitals/register/                         → create hospital
4. POST /hospitals/me/upload-logo/                   → upload logo
5. POST /hospitals/me/branches/                      → add branches
6. POST /hospitals/me/departments/                   → add departments
7. POST /hospitals/me/verification/submit/           → submit for verification
8. POST /hospitals/me/invite-user/                   → add HR/Recruiter
9. POST /jobs/                                       → post first job
```

---

## PART 10 — QUICK REFERENCE CHEAT SHEET

### Auth
| Action | API |
|--------|-----|
| Register | `POST /auth/register/` |
| Login | `POST /auth/login/` |
| OTP Send | `POST /auth/send-otp/` |
| OTP Verify | `POST /auth/verify-otp/` |
| Refresh Token | `POST /auth/refresh/` |
| Logout | `POST /auth/logout/` |
| Forgot Password | `POST /auth/password/forgot/` |
| Reset Password | `POST /auth/password/reset/` |

### Doctor
| Action | API |
|--------|-----|
| Create Profile | `POST /doctors/profile/` |
| Get My Profile | `GET /doctors/profile/me/` |
| Update Profile | `PATCH /doctors/profile/me/` |
| Upload Photo | `POST /doctors/profile/me/photo/` |
| Add Registration | `POST /doctors/profile/me/registrations/` |
| Submit Verification | `POST /doctors/profile/me/verification/submit/` |
| Check Verification | `GET /doctors/profile/me/verification/` |

### Jobs
| Action | API |
|--------|-----|
| Browse Jobs | `GET /jobs/` |
| Job Detail | `GET /jobs/{id}/` |
| Apply | `POST /jobs/{id}/apply/` |
| Withdraw | `POST /jobs/{id}/withdraw/` |
| Save Job | `POST /jobs/{id}/save/` |
| My Applications | `GET /jobs/my-applications/` |

### Feed
| Action | API |
|--------|-----|
| Home Screen | `GET /feed/home/` |
| Feed Posts | `GET /feed/` |
| Create Post | `POST /feed/posts/` |
| Like Post | `POST /feed/posts/{id}/like/` |
| Comments | `GET /feed/posts/{id}/comments/` |
| Add Comment | `POST /feed/posts/{id}/comments/` |

### Network
| Action | API |
|--------|-----|
| Send Request | `POST /network/connections/request/` |
| Accept | `POST /network/connections/{id}/accept/` |
| Reject | `POST /network/connections/{id}/reject/` |
| My Connections | `GET /network/connections/` |

### Messaging
| Action | API |
|--------|-----|
| Start Chat | `POST /messages/conversations/` |
| List Chats | `GET /messages/conversations/` |
| Get Messages | `GET /messages/conversations/{id}/messages/` |
| Send Message | `POST /messages/conversations/{id}/messages/` |
| Mark Read | `POST /messages/conversations/{id}/read/` |

### Availability & Shifts
| Action | API |
|--------|-----|
| Post Availability | `POST /availability/` |
| My Availabilities | `GET /availability/me/` |
| Browse Shifts | `GET /shifts/requirements/` |
| Request Shift | `POST /shifts/requirements/{id}/request/` |
| My Shift Requests | `GET /shifts/requests/mine/` |
| Accept/Decline Shift | `PATCH /shifts/requests/{id}/respond/` |
