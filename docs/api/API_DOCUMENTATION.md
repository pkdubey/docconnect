# DocConnect API Documentation
> **Version:** 1.0.0 | **Base URL:** `http://3.111.58.158/api/v1` | **Format:** JSON

---

## Global Contract

### Authentication
All protected endpoints require a Bearer token in the header:
```
Authorization: Bearer <access_token>
```

### Standard Response Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (delete success) |
| 400 | Bad Request / Validation Error |
| 401 | Unauthorized (invalid/expired token) |
| 403 | Forbidden (wrong role/permission) |
| 404 | Not Found |
| 409 | Conflict (duplicate) |
| 429 | Too Many Requests |
| 500 | Server Error |

### Error Response Format
```json
{ "detail": "Error message here" }
```

### Pagination
All list endpoints support:
```
?page=1&page_size=20
```
Response includes `total`, `page`, `page_size`.

---

## 1. AUTHENTICATION

### POST `/auth/register/`
Register a new doctor or hospital admin.

**Auth:** Not required

**Request Body:**
```json
{
  "first_name": "Arjun",
  "last_name": "Sharma",
  "phone": "9876543210",
  "password": "securepass123",
  "user_type": "DOCTOR",
  "email": "arjun@example.com"
}
```
- `user_type`: `DOCTOR` | `HOSPITAL_ADMIN` | `HOSPITAL_HR`
- `phone`: 10-digit Indian mobile (starts with 6-9)
- `password`: min 8 chars

**Response 201:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "uuid",
  "user_type": "DOCTOR",
  "profile_created": true
}
```

---

### POST `/auth/login/`
Login with phone + password.

**Auth:** Not required

**Request Body:**
```json
{
  "phone": "9876543210",
  "password": "securepass123",
  "user_type": "DOCTOR",
  "device_id": "optional-device-id"
}
```
- `user_type`: `DOCTOR` | `HOSPITAL_ADMIN` | `ADMIN`

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

---

### POST `/auth/send-otp/`
Send OTP to phone number.

**Auth:** Not required

**Request Body:**
```json
{
  "phone": "9876543210",
  "purpose": "LOGIN"
}
```
- `purpose`: `LOGIN` | `REGISTER` | `RESET_PASSWORD`

**Response 200:**
```json
{
  "success": true,
  "message": "OTP sent",
  "expires_in": 300,
  "otp": "123456"
}
```
> Note: `otp` field only returned in dev/debug mode.

---

### POST `/auth/verify-otp/`
Verify OTP and get tokens.

**Auth:** Not required

**Request Body:**
```json
{
  "phone": "9876543210",
  "otp": "123456",
  "purpose": "LOGIN",
  "user_type": "DOCTOR",
  "device_id": "optional"
}
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

---

### POST `/auth/refresh/`
Refresh access token.

**Auth:** Not required

**Request Body:**
```json
{ "refresh_token": "eyJ..." }
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

---

### POST `/auth/logout/`
Logout and blacklist token.

**Auth:** Required

**Response 200:**
```json
{ "success": true, "message": "Logged out" }
```

---

### POST `/auth/password/forgot/`
Send OTP for password reset.

**Auth:** Not required

**Request Body:**
```json
{ "phone": "9876543210" }
```

**Response 200:**
```json
{
  "success": true,
  "message": "OTP sent",
  "expires_in": 300
}
```

---

### POST `/auth/password/reset/`
Reset password using OTP.

**Auth:** Not required

**Request Body:**
```json
{
  "phone": "9876543210",
  "otp": "123456",
  "new_password": "newpass123"
}
```

**Response 200:**
```json
{ "success": true, "message": "Password reset successfully" }
```

---

### POST `/auth/password/change/`
Change password (authenticated user).

**Auth:** Required

**Request Body:**
```json
{
  "old_password": "oldpass123",
  "new_password": "newpass123"
}
```

**Response 200:**
```json
{ "success": true, "message": "Password changed successfully" }
```

---

### GET `/auth/sessions/`
List active sessions/devices.

**Auth:** Required

**Response 200:**
```json
{
  "sessions": [
    {
      "id": "uuid",
      "device_name": "iPhone 15",
      "ip_address": "192.168.1.1",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

### DELETE `/auth/sessions/{id}/`
Revoke a specific session.

**Auth:** Required

**Response 200:**
```json
{ "success": true, "message": "Session revoked" }
```

---

### POST `/auth/sessions/revoke-all/`
Revoke all sessions.

**Auth:** Required

**Response 200:**
```json
{ "success": true, "message": "All sessions revoked" }
```

---

### DELETE `/account/`
Deactivate/delete account.

**Auth:** Required

**Response 200:**
```json
{ "success": true, "message": "Account deactivated" }
```

---

## 2. DOCTOR PROFILE

### POST `/doctors/profile/`
Create doctor profile.

**Auth:** Required (DOCTOR only)

**Request Body:**
```json
{
  "first_name": "Arjun",
  "last_name": "Sharma",
  "headline": "Cardiologist · AIIMS Delhi · 12 yrs",
  "about": "Senior cardiologist with 12 years experience.",
  "primary_specialization_id": "uuid",
  "clinical_interests": ["uuid1", "uuid2"],
  "professional_location": {
    "address": "123 Main St",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "coordinates": { "lat": 19.076, "lng": 72.877 }
  },
  "experience_years": 12.0
}
```

**Response 201:** Doctor profile object (see GET /doctors/profile/me/)

---

### GET `/doctors/profile/me/`
Get my profile.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "first_name": "Arjun",
  "last_name": "Sharma",
  "full_name": "Arjun Sharma",
  "photo_file_id": "uuid or null",
  "headline": "Cardiologist · AIIMS Delhi · 12 yrs",
  "about": "Senior cardiologist...",
  "primary_specialization_id": "uuid",
  "clinical_interests": ["uuid"],
  "professional_location": { "city": "Mumbai", "state": "Maharashtra" },
  "experience_years": 12.0,
  "open_to_opportunities": true,
  "verification_status": "VERIFIED",
  "is_verified": true,
  "languages": ["English", "Hindi"],
  "career_preferences": {},
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

---

### PATCH `/doctors/profile/me/`
Update my profile (partial update).

**Auth:** Required (DOCTOR)

**Request Body:** (all fields optional)
```json
{
  "headline": "Updated headline",
  "about": "Updated bio",
  "experience_years": 13.0,
  "open_to_opportunities": true,
  "languages": ["English", "Hindi", "Marathi"],
  "career_preferences": { "preferred_job_types": ["FULL_TIME"] }
}
```

**Response 200:** Updated doctor profile object

---

### GET `/doctors/profile/{doctor_id}/`
View any doctor's profile by ID.

**Auth:** Required

**Response 200:** Doctor profile object
> Returns 403 if profile is private/connections-only

---

### POST `/doctors/profile/me/photo/`
Upload profile photo.

**Auth:** Required (DOCTOR)

**Request:** `multipart/form-data`
- `file`: image file (JPEG/PNG/WEBP only)

**Response 200:**
```json
{ "success": true, "file_id": "uuid" }
```

---

### GET `/doctors/search/`
Search doctors.

**Auth:** Required

**Query Params:**
| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Name/headline search |
| `specialty` | uuid | Specialization ID |
| `city` | string | City filter |
| `experience_min` | float | Min years experience |
| `open_to_opportunities` | bool | Available doctors only |
| `page` | int | Default: 1 |
| `page_size` | int | Default: 20, max: 100 |

**Response 200:**
```json
{
  "total": 50,
  "page": 1,
  "page_size": 20,
  "results": [ /* doctor profile objects */ ]
}
```

---

### POST `/doctors/profile/me/registrations/`
Add NMC/council registration.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{
  "council_id": "uuid",
  "registration_number": "MH-12345",
  "registration_year": 2010,
  "is_primary": true
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "registration_number": "MH-12345",
  "verification_status": "PENDING"
}
```

---

### GET `/doctors/profile/me/registrations/`
List my registrations.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
[
  {
    "id": "uuid",
    "council_id": "uuid",
    "registration_number": "MH-12345",
    "registration_year": 2010,
    "is_primary": true,
    "verification_status": "PENDING"
  }
]
```

---

### POST `/doctors/profile/me/qualifications/`
Add qualification.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{
  "degree": "MBBS",
  "institution": "AIIMS Delhi",
  "year": 2010,
  "specialization": "Cardiology"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "degree": "MBBS",
  "institution": "AIIMS Delhi",
  "year": 2010,
  "specialization": "Cardiology"
}
```

---

### GET `/doctors/profile/me/qualifications/`
List qualifications.

**Auth:** Required (DOCTOR)

**Response 200:** Array of qualification objects

---

### DELETE `/doctors/profile/me/qualifications/{id}/`
Delete qualification.

**Auth:** Required (DOCTOR)

**Response 204:** No content

---

### POST `/doctors/profile/me/experiences/`
Add work experience.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{
  "role": "Senior Cardiologist",
  "hospital_name": "Apollo Hospital",
  "location": "Mumbai",
  "start_date": "2015-01-01",
  "end_date": null,
  "is_current": true,
  "description": "Leading cardiac care unit"
}
```

**Response 201:** Experience object

---

### GET `/doctors/profile/me/experiences/`
List experiences.

**Auth:** Required (DOCTOR)

**Response 200:** Array of experience objects

---

### PATCH `/doctors/profile/me/experiences/{id}/`
Update experience.

**Auth:** Required (DOCTOR)

**Request Body:** Same as POST experiences

**Response 200:** Updated experience object

---

### DELETE `/doctors/profile/me/experiences/{id}/`
Delete experience.

**Auth:** Required (DOCTOR)

**Response 204:** No content

---

### POST `/doctors/profile/me/affiliations/`
Add hospital affiliation.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{
  "hospital_name": "Apollo Hospital",
  "role": "Visiting Consultant",
  "start_date": "2020-01-01",
  "end_date": null,
  "is_current": true
}
```

**Response 201:** Affiliation object

---

### GET `/doctors/profile/me/affiliations/`
List affiliations.

**Auth:** Required (DOCTOR)

**Response 200:** Array of affiliation objects

---

### PATCH `/doctors/profile/me/affiliations/{id}/`
Update affiliation.

**Auth:** Required (DOCTOR)

**Response 200:** Updated affiliation object

---

### DELETE `/doctors/profile/me/affiliations/{id}/`
Delete affiliation.

**Auth:** Required (DOCTOR)

**Response 204:** No content

---

### GET `/doctors/profile/me/verification/`
Get verification status.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{
  "verification_status": "PENDING",
  "is_verified": false,
  "rejected_reason": null
}
```
- `verification_status`: `UNVERIFIED` | `PENDING` | `VERIFIED` | `REJECTED`

---

### POST `/doctors/profile/me/verification/submit/`
Submit for verification (requires at least 1 registration added).

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{
  "success": true,
  "verification_status": "PENDING",
  "message": "Verification submitted for review"
}
```

---

### POST `/doctors/profile/me/verification/resubmit/`
Resubmit after rejection.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{ "success": true, "verification_status": "PENDING" }
```

---

### GET `/doctors/profile/me/status/`
Get professional status.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{
  "open_to_opportunities": true,
  "career_visibility": "VERIFIED_HOSPITALS",
  "verification_status": "VERIFIED"
}
```

---

### PUT `/doctors/profile/me/status/`
Update professional status.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{
  "open_to_opportunities": true,
  "career_visibility": "VERIFIED_HOSPITALS"
}
```
- `career_visibility`: `VERIFIED_HOSPITALS` | `SELECTED_HOSPITALS` | `HIDDEN`

**Response 200:**
```json
{
  "success": true,
  "open_to_opportunities": true,
  "career_visibility": "VERIFIED_HOSPITALS"
}
```

---

### GET `/doctors/profile/me/privacy/`
Get privacy settings.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{
  "profile_visibility": "EVERYONE",
  "career_visibility": "VERIFIED_HOSPITALS"
}
```

---

### PUT `/doctors/profile/me/privacy/`
Update privacy settings.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{
  "profile_visibility": "DOCTORS_ONLY",
  "career_visibility": "VERIFIED_HOSPITALS"
}
```
- `profile_visibility`: `EVERYONE` | `DOCTORS_ONLY` | `CONNECTIONS_ONLY`

**Response 200:**
```json
{ "success": true, "profile_visibility": "DOCTORS_ONLY", "career_visibility": "VERIFIED_HOSPITALS" }
```

---

### GET `/doctors/me/saved-jobs/`
List saved jobs.

**Auth:** Required (DOCTOR)

**Query Params:** `page`, `page_size`

**Response 200:**
```json
{
  "total": 5,
  "page": 1,
  "results": [
    {
      "id": "uuid",
      "title": "Senior Cardiologist",
      "hospital_name": "Apollo Hospital",
      "job_type": "FULL_TIME",
      "location": { "city": "Mumbai" },
      "is_urgent": false
    }
  ]
}
```

---

### GET `/doctors/me/job-recommendations/`
Get AI-recommended jobs for doctor.

**Auth:** Required (DOCTOR)

**Query Params:** `page`, `page_size`

**Response 200:**
```json
{
  "total": 10,
  "page": 1,
  "results": [
    {
      "id": "uuid",
      "title": "Senior Cardiologist",
      "hospital_name": "Apollo Hospital",
      "job_type": "FULL_TIME",
      "location": {},
      "is_urgent": false,
      "salary_min": "150000",
      "salary_visibility": "PUBLIC"
    }
  ]
}
```

---

## 3. HOSPITALS

### POST `/hospitals/register/`
Register a new hospital.

**Auth:** Required (HOSPITAL_ADMIN)

**Request Body:**
```json
{
  "name": "Apollo Hospital",
  "type": "HOSPITAL",
  "about": "Multi-specialty hospital",
  "location": {
    "address": "123 Main St",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001"
  },
  "bed_count": 500,
  "hospital_phone": "9876543210",
  "hospital_email": "info@apollo.com",
  "website": "https://apollo.com"
}
```
- `type`: `HOSPITAL` | `CLINIC` | `NURSING_HOME` | `MEDICAL_COLLEGE`

**Response 201:** Hospital object

---

### GET `/hospitals/me/`
Get my hospital profile.

**Auth:** Required (Hospital user)

**Response 200:**
```json
{
  "id": "uuid",
  "name": "Apollo Hospital",
  "type": "HOSPITAL",
  "about": "Multi-specialty hospital",
  "location": { "city": "Mumbai", "state": "Maharashtra" },
  "bed_count": 500,
  "phone": "9876543210",
  "email": "info@apollo.com",
  "website": "https://apollo.com",
  "verification_status": "VERIFIED",
  "logo_file_id": null,
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

### PATCH `/hospitals/me/`
Update hospital profile.

**Auth:** Required (HOSPITAL_ADMIN)

**Request Body:** (all optional)
```json
{
  "name": "Apollo Hospital Updated",
  "about": "Updated description",
  "bed_count": 600,
  "hospital_phone": "9876543210",
  "hospital_email": "new@apollo.com",
  "website": "https://apollo.com"
}
```

**Response 200:** Updated hospital object

---

### POST `/hospitals/me/verification/submit/`
Submit hospital for verification.

**Auth:** Required (HOSPITAL_ADMIN)

**Response 200:**
```json
{ "success": true, "verification_status": "PENDING", "hospital_id": "uuid" }
```

---

### GET `/hospitals/me/verification/`
Get hospital verification status.

**Auth:** Required (Hospital user)

**Response 200:**
```json
{
  "verification_status": "VERIFIED",
  "verified_at": "2025-01-01T00:00:00Z"
}
```

---

### POST `/hospitals/me/branches/`
Add a branch.

**Auth:** Required (HOSPITAL_ADMIN)

**Request Body:**
```json
{
  "name": "Andheri Branch",
  "location": { "city": "Mumbai", "state": "Maharashtra", "pincode": "400053" },
  "phone": "9876543210",
  "is_primary": false
}
```

**Response 201:**
```json
{ "id": "uuid", "name": "Andheri Branch", "is_primary": false }
```

---

### GET `/hospitals/me/branches/`
List branches.

**Auth:** Required (Hospital user)

**Response 200:**
```json
[
  {
    "id": "uuid",
    "name": "Andheri Branch",
    "location": { "city": "Mumbai" },
    "phone": "9876543210",
    "is_primary": false
  }
]
```

---

### PATCH `/hospitals/me/branches/{id}/`
Update branch.

**Auth:** Required (HOSPITAL_ADMIN)

**Request Body:** Same as POST branches

**Response 200:** Updated branch object

---

### DELETE `/hospitals/me/branches/{id}/`
Deactivate branch.

**Auth:** Required (HOSPITAL_ADMIN)

**Response 204:** No content

---

### POST `/hospitals/me/departments/`
Add department.

**Auth:** Required (HOSPITAL_ADMIN)

**Request Body:**
```json
{
  "name": "Cardiology",
  "branch_id": "uuid or null"
}
```

**Response 201:**
```json
{ "id": "uuid", "name": "Cardiology" }
```

---

### GET `/hospitals/me/departments/`
List departments.

**Auth:** Required (Hospital user)

**Response 200:**
```json
[
  { "id": "uuid", "name": "Cardiology", "branch_id": null, "active": true }
]
```

---

### POST `/hospitals/me/invite-user/`
Invite HR/Recruiter to hospital.

**Auth:** Required (HOSPITAL_ADMIN)

**Request Body:**
```json
{
  "phone": "9876543210",
  "role": "HR",
  "designation": "HR Manager",
  "branch_id": "uuid or null",
  "department_id": "uuid or null"
}
```
- `role`: `ADMIN` | `HR` | `RECRUITER`

**Response 201:**
```json
{ "success": true, "message": "9876543210 added as HR" }
```

---

### POST `/hospitals/me/users/`
Add hospital user.

**Auth:** Required (HOSPITAL_ADMIN)

**Request Body:** Same as invite-user

**Response 201:**
```json
{ "success": true, "message": "9876543210 added as HR" }
```

---

### GET `/hospitals/me/users/`
List hospital users.

**Auth:** Required (HOSPITAL_ADMIN)

**Response 200:** Array of staff objects

---

### PATCH `/hospitals/me/users/{id}/`
Update user role/branch/status.

**Auth:** Required (HOSPITAL_ADMIN)

**Request Body:**
```json
{
  "role": "RECRUITER",
  "designation": "Senior Recruiter",
  "branch_id": "uuid",
  "status": "ACTIVE"
}
```

**Response 200:**
```json
{ "success": true, "message": "User updated" }
```

---

### DELETE `/hospitals/me/users/{id}/`
Revoke user membership.

**Auth:** Required (HOSPITAL_ADMIN)

**Response 204:** No content

---

### GET `/hospitals/me/staff/`
List all hospital staff.

**Auth:** Required (HOSPITAL_ADMIN)

**Response 200:**
```json
[
  {
    "user_id": "uuid",
    "phone": "9876543210",
    "role": "HR",
    "designation": "HR Manager",
    "status": "ACTIVE"
  }
]
```

---

### POST `/hospitals/me/upload-logo/`
Upload hospital logo.

**Auth:** Required (HOSPITAL_ADMIN)

**Request:** `multipart/form-data`
- `file`: image (JPEG/PNG/WEBP)

**Response 200:**
```json
{ "success": true, "file_id": "uuid" }
```

---

### GET `/hospitals/me/candidates/`
Search & filter doctors (candidate discovery).

**Auth:** Required (Hospital user)

**Query Params:**
| Param | Type | Description |
|-------|------|-------------|
| `specialty` | uuid | Specialization ID |
| `qualification` | string | Qualification filter |
| `experience_min` | float | Min years |
| `city` | string | City |
| `state` | string | State |
| `verified_only` | bool | Default: true |
| `available_now` | bool | Currently available |
| `locum_available` | bool | Locum availability |
| `visiting_available` | bool | Visiting availability |
| `search` | string | Name search |
| `page` | int | Default: 1 |
| `page_size` | int | Default: 20 |

**Response 200:**
```json
{
  "total": 25,
  "page": 1,
  "results": [
    {
      "id": "uuid",
      "full_name": "Arjun Sharma",
      "headline": "Cardiologist · 12 yrs",
      "experience_years": 12.0,
      "verification_status": "VERIFIED",
      "open_to_opportunities": true,
      "location": { "city": "Mumbai" },
      "primary_specialization_id": "uuid"
    }
  ]
}
```

---

### GET `/hospitals/{id}/`
View public hospital profile.

**Auth:** Required

**Response 200:** Hospital object (verified hospitals only)

---

## 4. JOBS

### POST `/jobs/`
Create a job posting (auto-published).

**Auth:** Required (Hospital user)

**Request Body:**
```json
{
  "title": "Senior Cardiologist",
  "specialty_id": "uuid",
  "qualification_ids": ["uuid1", "uuid2"],
  "description": "Looking for experienced cardiologist...",
  "responsibilities": "Lead cardiac care unit",
  "requirements": "MBBS + MD Cardiology",
  "location": { "city": "Mumbai", "state": "Maharashtra" },
  "salary_min": 150000,
  "salary_max": 250000,
  "salary_visibility": "PUBLIC",
  "currency": "INR",
  "job_type": "FULL_TIME",
  "experience_min_years": 5,
  "experience_max_years": 15,
  "shift_type": "DAY",
  "joining_requirement": "Immediate",
  "positions": 2,
  "is_urgent": false,
  "closing_date": "2025-12-31T00:00:00Z"
}
```
- `job_type`: `FULL_TIME` | `PART_TIME` | `VISITING` | `LOCUM` | `CONTRACT`
- `salary_visibility`: `PUBLIC` | `ON_REQUEST` | `HIDDEN`
- `shift_type`: `DAY` | `NIGHT` | `ROTATIONAL` | `FLEXIBLE`

**Response 201:**
```json
{
  "id": "uuid",
  "title": "Senior Cardiologist",
  "status": "PUBLISHED",
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

### GET `/jobs/`
List published jobs with filters.

**Auth:** Required

**Query Params:**
| Param | Type | Description |
|-------|------|-------------|
| `specialty` | uuid | Specialization ID |
| `city` | string | City filter |
| `job_type` | string | FULL_TIME/LOCUM etc. |
| `search` | string | Full-text search |
| `is_urgent` | bool | Urgent jobs only |
| `experience_max` | float | Max experience required |
| `page` | int | Default: 1 |
| `page_size` | int | Default: 20 |

**Response 200:**
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": "uuid",
      "title": "Senior Cardiologist",
      "hospital_name": "Apollo Hospital",
      "job_type": "FULL_TIME",
      "location": { "city": "Mumbai" },
      "is_urgent": false,
      "salary_min": "150000",
      "salary_max": "250000",
      "salary_visibility": "PUBLIC",
      "published_at": "2025-01-01T00:00:00Z",
      "match_score": 85,
      "match_factors": ["Specialization match", "Experience match"]
    }
  ]
}
```

---

### GET `/jobs/{id}/`
Get job details.

**Auth:** Required

**Response 200:**
```json
{
  "id": "uuid",
  "title": "Senior Cardiologist",
  "hospital_id": "uuid",
  "hospital_name": "Apollo Hospital",
  "description": "...",
  "responsibilities": "...",
  "requirements": "...",
  "location": { "city": "Mumbai", "state": "Maharashtra" },
  "job_type": "FULL_TIME",
  "shift_type": "DAY",
  "experience_min_years": 5.0,
  "experience_max_years": 15.0,
  "salary_min": "150000",
  "salary_max": "250000",
  "salary_visibility": "PUBLIC",
  "positions": 2,
  "is_urgent": false,
  "closing_date": "2025-12-31T00:00:00Z"
}
```

---

### PATCH `/jobs/{id}/`
Update job posting.

**Auth:** Required (Hospital user)

**Request Body:** (all optional)
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "salary_min": 160000,
  "salary_max": 260000,
  "is_urgent": true,
  "positions": 3,
  "closing_date": "2025-12-31T00:00:00Z"
}
```

**Response 200:** Updated job object

---

### POST `/jobs/{id}/publish/`
Publish a draft job.

**Auth:** Required (Hospital user)

**Response 200:**
```json
{ "success": true, "status": "PUBLISHED" }
```

---

### POST `/jobs/{id}/close/`
Close a job posting.

**Auth:** Required (Hospital user)

**Response 200:**
```json
{ "success": true, "status": "CLOSED" }
```

---

### POST `/jobs/{id}/apply/`
One-tap apply to a job.

**Auth:** Required (DOCTOR)

**Query Params:**
- `cv_file_id` (optional): UUID of uploaded CV file

**Response 201:**
```json
{
  "success": true,
  "application_id": "uuid",
  "status": "APPLIED"
}
```

---

### POST `/jobs/{id}/withdraw/`
Withdraw job application.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{ "success": true, "status": "WITHDRAWN" }
```

---

### POST `/jobs/{id}/save/`
Save a job.

**Auth:** Required (DOCTOR)

**Response 201:**
```json
{ "success": true, "message": "Job saved" }
```

---

### DELETE `/jobs/{id}/save/`
Unsave a job.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{ "success": true, "message": "Job unsaved" }
```

---

### GET `/jobs/my-applications/`
Doctor's job applications.

**Auth:** Required (DOCTOR)

**Query Params:**
- `status`: `APPLIED` | `SHORTLISTED` | `INTERVIEW` | `OFFERED` | `HIRED` | `REJECTED` | `WITHDRAWN`
- `page`, `page_size`

**Response 200:**
```json
{
  "total": 5,
  "page": 1,
  "results": [
    {
      "application_id": "uuid",
      "job_id": "uuid",
      "job_title": "Senior Cardiologist",
      "hospital_name": "Apollo Hospital",
      "status": "APPLIED",
      "applied_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

### GET `/jobs/{id}/applications/`
Hospital — list applicants for a job.

**Auth:** Required (Hospital user)

**Query Params:** `status`, `page`, `page_size`

**Response 200:**
```json
{
  "total": 10,
  "page": 1,
  "results": [
    {
      "application_id": "uuid",
      "doctor_id": "uuid",
      "doctor_name": "Arjun Sharma",
      "status": "APPLIED",
      "applied_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

### PATCH `/jobs/applications/{id}/status/`
Update application status (hospital).

**Auth:** Required (Hospital user)

**Request Body:**
```json
{
  "status": "SHORTLISTED",
  "notes": "Strong candidate"
}
```
- `status`: `PROFILE_VIEWED` | `SHORTLISTED` | `INTERVIEW` | `OFFERED` | `HIRED` | `REJECTED`

**Response 200:**
```json
{ "success": true, "application_id": "uuid", "status": "SHORTLISTED" }
```

---

### POST `/applications/{id}/interview/`
Schedule interview.

**Auth:** Required (Hospital user)

**Request Body:**
```json
{
  "scheduled_at": "2025-08-20T10:00:00Z",
  "mode": "VIDEO",
  "notes": "Technical round"
}
```
- `mode`: `IN_PERSON` | `VIDEO` | `PHONE`

**Response 201:**
```json
{ "success": true, "interview_id": "uuid", "scheduled_at": "2025-08-20T10:00:00Z" }
```

---

### PATCH `/applications/{id}/interview/{interview_id}/`
Update interview outcome.

**Auth:** Required (Hospital user)

**Query Params:**
- `outcome`: `PASS` | `FAIL` | `PENDING`
- `notes` (optional)

**Response 200:**
```json
{ "success": true, "interview_id": "uuid", "outcome": "PASS" }
```

---

### POST `/applications/{id}/offer/`
Send offer to candidate.

**Auth:** Required (Hospital user)

**Request Body:**
```json
{
  "salary": "200000",
  "joining_date": "2025-09-01",
  "notes": "Offer letter attached"
}
```

**Response 201:**
```json
{ "success": true, "status": "OFFERED" }
```

---

### POST `/applications/{id}/notes/`
Add internal HR note to application.

**Auth:** Required (Hospital user)

**Request Body:**
```json
{ "note": "Strong candidate, good communication skills" }
```

**Response 201:**
```json
{ "success": true, "note_id": "uuid" }
```

---

### GET `/applications/{id}/notes/`
List application notes.

**Auth:** Required (Hospital user)

**Response 200:**
```json
{
  "notes": [
    {
      "id": "uuid",
      "note": "Strong candidate",
      "added_by": "uuid",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

---

### POST `/applications/{id}/invite/`
Invite doctor to apply for a job.

**Auth:** Required (Hospital user)

**Request Body:**
```json
{
  "doctor_id": "uuid",
  "job_id": "uuid"
}
```

**Response 201:**
```json
{ "success": true, "application_id": "uuid", "status": "INVITED" }
```

---

### GET `/jobs/{id}/matches/`
Get matched doctors for a job (AI matching).

**Auth:** Required (Hospital user)

**Query Params:** `page`, `page_size`

**Response 200:**
```json
{
  "job_id": "uuid",
  "total": 15,
  "page": 1,
  "matched_doctors": [
    {
      "doctor_id": "uuid",
      "full_name": "Dr. Arjun Sharma",
      "headline": "Cardiologist · 12 yrs",
      "experience_years": 12.0,
      "verification_status": "VERIFIED",
      "location": { "city": "Mumbai" }
    }
  ]
}
```

---

### GET `/jobs/recommendations/`
Get recommended jobs for doctor.

**Auth:** Required (DOCTOR)

**Query Params:** `page`, `page_size`

**Response 200:**
```json
{
  "total": 10,
  "page": 1,
  "results": [ /* job list items */ ]
}
```

---

## 5. AVAILABILITY

### POST `/availability/`
Doctor posts availability with time slots.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{
  "availability_type": "LOCUM",
  "available_from": "2025-08-15",
  "available_until": "2025-08-30",
  "preferred_location": {
    "city": "Mumbai",
    "state": "Maharashtra"
  },
  "preferred_radius_km": 50,
  "minimum_compensation": 8000,
  "currency": "INR",
  "notes": "Available weekdays only",
  "slots": [
    {
      "slot_date": "2025-08-15",
      "start_time": "09:00:00",
      "end_time": "17:00:00"
    },
    {
      "slot_date": "2025-08-16",
      "start_time": "09:00:00",
      "end_time": "17:00:00"
    }
  ]
}
```
- `availability_type`: `LOCUM` | `VISITING` | `TEMPORARY` | `PART_TIME`

**Response 201:**
```json
{
  "success": true,
  "availability_id": "uuid",
  "slots_created": 2
}
```

---

### GET `/availability/me/`
List my availabilities.

**Auth:** Required (DOCTOR)

**Query Params:**
- `is_active`: `true` | `false`

**Response 200:**
```json
[
  {
    "id": "uuid",
    "availability_type": "LOCUM",
    "available_from": "2025-08-15",
    "available_until": "2025-08-30",
    "preferred_location": { "city": "Mumbai" },
    "preferred_radius_km": 50,
    "minimum_compensation": "8000",
    "currency": "INR",
    "notes": null,
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

---

### PATCH `/availability/{id}/`
Update availability.

**Auth:** Required (DOCTOR)

**Request Body:** (all optional)
```json
{
  "available_from": "2025-08-20",
  "available_until": "2025-09-05",
  "minimum_compensation": 10000,
  "preferred_radius_km": 30,
  "is_active": true,
  "notes": "Updated notes"
}
```

**Response 200:** Updated availability object

---

### DELETE `/availability/{id}/`
Deactivate availability.

**Auth:** Required (DOCTOR)

> Returns 409 if there are pending/confirmed shift requests linked to this availability.

**Response 204:** No content

---

### GET `/availability/{id}/slots/`
List slots for an availability.

**Auth:** Required

**Response 200:**
```json
[
  {
    "id": "uuid",
    "slot_date": "2025-08-15",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "is_booked": false
  }
]
```

---

### POST `/availability/{id}/slots/`
Add a slot to availability.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{
  "slot_date": "2025-08-17",
  "start_time": "09:00:00",
  "end_time": "17:00:00"
}
```

> Returns 409 if slot overlaps with an accepted/confirmed shift.

**Response 201:** Slot object

---

### PATCH `/availability/slots/{slot_id}/`
Update a slot.

**Auth:** Required (DOCTOR)

**Request Body:** Same as POST slot

**Response 200:** Updated slot object

---

### DELETE `/availability/slots/{slot_id}/`
Delete a slot.

**Auth:** Required (DOCTOR)

**Response 204:** No content

---

### GET `/availability/preferences/`
Get availability preferences.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{
  "preferences": {
    "preferred_availability_types": ["LOCUM", "VISITING"],
    "preferred_radius_km": 50,
    "minimum_compensation": 8000,
    "currency": "INR",
    "auto_accept": false
  }
}
```

---

### PUT `/availability/preferences/`
Update availability preferences.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{
  "preferred_availability_types": ["LOCUM"],
  "preferred_radius_km": 30,
  "minimum_compensation": 10000,
  "currency": "INR",
  "auto_accept": false
}
```

**Response 200:**
```json
{ "success": true, "preferences": { ... } }
```

---

## 6. SHIFTS

### POST `/shifts/requirements/`
Hospital posts a shift requirement.

**Auth:** Required (Hospital user)

**Request Body:**
```json
{
  "specialty_id": "uuid",
  "qualification_ids": ["uuid"],
  "requirement_date": "2025-08-18",
  "start_time": "08:00:00",
  "end_time": "20:00:00",
  "location": { "city": "Mumbai", "state": "Maharashtra" },
  "compensation": 12000,
  "currency": "INR",
  "doctors_required": 2,
  "urgency": "URGENT",
  "notes": "ICU coverage needed",
  "branch_id": "uuid or null"
}
```
- `urgency`: `NORMAL` | `URGENT` | `IMMEDIATE`

**Response 201:**
```json
{
  "id": "uuid",
  "hospital_id": "uuid",
  "specialty_id": "uuid",
  "requirement_date": "2025-08-18",
  "start_time": "08:00:00",
  "end_time": "20:00:00",
  "location": { "city": "Mumbai" },
  "compensation": "12000",
  "currency": "INR",
  "doctors_required": 2,
  "urgency": "URGENT",
  "status": "OPEN",
  "notes": "ICU coverage needed",
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

### GET `/shifts/requirements/`
List open shift requirements.

**Auth:** Required

**Query Params:**
| Param | Type | Description |
|-------|------|-------------|
| `urgency` | string | NORMAL/URGENT/IMMEDIATE |
| `city` | string | City filter |
| `specialty` | uuid | Specialization ID |
| `page` | int | Default: 1 |
| `page_size` | int | Default: 20 |

**Response 200:**
```json
{
  "total": 10,
  "page": 1,
  "results": [ /* shift requirement objects */ ]
}
```

---

### GET `/shifts/requirements/mine/`
Hospital's own shift requirements.

**Auth:** Required (Hospital user)

**Response 200:** Array of shift requirement objects

---

### PATCH `/shifts/requirements/{id}/`
Update shift requirement.

**Auth:** Required (Hospital user)

**Request Body:** (all optional)
```json
{
  "doctors_required": 3,
  "urgency": "IMMEDIATE",
  "notes": "Updated notes",
  "compensation": 15000
}
```

**Response 200:** Updated shift requirement object

---

### GET `/shifts/requirements/{id}/matched-doctors/`
Get matched doctors for a shift requirement.

**Auth:** Required (Hospital user)

**Response 200:**
```json
{
  "total": 5,
  "matched_doctors": [
    {
      "doctor_id": "uuid",
      "full_name": "Arjun Sharma",
      "headline": "Anesthesiologist · 8 yrs",
      "experience_years": 8.0,
      "verification_status": "VERIFIED",
      "availability_id": "uuid",
      "minimum_compensation": "8000"
    }
  ]
}
```

---

### POST `/shifts/requirements/{id}/match/`
Get matched doctors (POST alias).

**Auth:** Required (Hospital user)

**Response 200:** Same as GET matched-doctors

---

### POST `/shifts/requirements/{id}/request/`
Hospital sends shift request to a doctor.

**Auth:** Required (DOCTOR)

> Doctor must have active availability covering the requirement date.
> Returns 409 if overlapping shift already accepted/confirmed.

**Response 201:**
```json
{ "success": true, "status": "REQUESTED" }
```

---

### PATCH `/shifts/requests/{id}/respond/`
Doctor accepts or declines a shift request.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{ "accept": true }
```

**Response 200:**
```json
{ "success": true, "status": "ACCEPTED_BY_DOCTOR" }
```
- Status becomes `ACCEPTED_BY_DOCTOR` or `DECLINED_BY_DOCTOR`

---

### PATCH `/shifts/requests/{id}/confirm/`
Hospital confirms shift after doctor accepts.

**Auth:** Required (Hospital user)

**Response 200:**
```json
{ "success": true, "status": "CONFIRMED_BY_HOSPITAL" }
```

---

### PATCH `/shifts/requests/{id}/complete/`
Hospital marks shift as completed.

**Auth:** Required (Hospital user)

**Response 200:**
```json
{ "success": true, "status": "COMPLETED" }
```

---

### PATCH `/shifts/requests/{id}/cancel/`
Cancel a shift request (doctor or hospital).

**Auth:** Required

**Response 200:**
```json
{ "success": true, "status": "CANCELLED" }
```

---

### GET `/shifts/requests/mine/`
Doctor's shift requests.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
[
  {
    "id": "uuid",
    "requirement_id": "uuid",
    "hospital_name": "Apollo Hospital",
    "requirement_date": "2025-08-18",
    "start_time": "08:00:00",
    "end_time": "20:00:00",
    "compensation": "12000",
    "urgency": "URGENT",
    "status": "REQUESTED",
    "requested_at": "2025-01-01T00:00:00Z"
  }
]
```

---

### GET `/shifts/requests/{id}/history/`
Shift request state history.

**Auth:** Required

**Response 200:**
```json
{
  "request_id": "uuid",
  "current_status": "CONFIRMED_BY_HOSPITAL",
  "history": [
    { "status": "REQUESTED", "timestamp": "2025-08-15T10:00:00Z" },
    { "status": "ACCEPTED_BY_DOCTOR", "timestamp": "2025-08-15T11:00:00Z" },
    { "status": "CONFIRMED_BY_HOSPITAL", "timestamp": "2025-08-15T12:00:00Z" }
  ]
}
```

---

## 7. FEED & POSTS

### GET `/feed/home/`
Home page summary — single API for mobile home screen.

**Auth:** Required

**Response 200:**
```json
{
  "stats": {
    "doctors": 1500,
    "hospitals": 200,
    "jobs": 350
  },
  "urgent_jobs": [
    {
      "id": "uuid",
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
      "id": "uuid",
      "full_name": "Dr. Priya Mehta",
      "headline": "Neurologist · 8 yrs",
      "photo": null,
      "initials": "PM",
      "color": "#0a66c2",
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

### GET `/feed/`
Paginated feed posts.

**Auth:** Required

**Query Params:**
- `page`: Default 1
- `page_size`: Default 10, max 50

**Response 200:**
```json
{
  "posts": [
    {
      "id": "uuid",
      "author": "Dr. Arjun Sharma",
      "author_id": "uuid",
      "headline": "Cardiologist · 12 yrs",
      "initials": "AS",
      "color": "#0a66c2",
      "photo": null,
      "post_type": "UPDATE",
      "post_type_display": "Update",
      "content": "Excited to share my latest research...",
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

### POST `/feed/posts/`
Create a new post.

**Auth:** Required

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | Post text |
| `post_type` | string | No | `UPDATE`(default)/`CASE`/`ARTICLE`/`PHOTO` |
| `is_anonymous` | bool | No | Anonymous post (CASE type, doctors only) |
| `patient_privacy_confirmed` | bool | Required for CASE | Confirms no patient PII |
| `image` | file | No | JPEG/PNG/WEBP, max 5MB |

**Response 201:**
```json
{
  "success": true,
  "post_id": "uuid",
  "author": "Dr. Arjun Sharma",
  "post_type": "Update",
  "content": "Post content here",
  "image": null,
  "pii_flagged": false,
  "created_at": "Just now"
}
```

---

### PATCH `/feed/posts/{id}/`
Edit own post.

**Auth:** Required

**Request:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `content` | string | Updated content |
| `remove_image` | bool | Set true to remove image |
| `image` | file | New image to replace |

**Response 200:**
```json
{ "success": true, "content": "Updated content", "image": null }
```

---

### DELETE `/feed/posts/{id}/`
Delete own post.

**Auth:** Required

**Response 200:**
```json
{ "success": true }
```

---

### POST `/feed/posts/{id}/like/`
Like or unlike a post (toggle).

**Auth:** Required

**Response 200:**
```json
{ "liked": true, "count": 25 }
```

---

### GET `/feed/posts/{id}/comments/`
Get comments for a post (with nested replies).

**Auth:** Required

**Response 200:**
```json
{
  "comments": [
    {
      "id": "uuid",
      "author": "Dr. Priya Mehta",
      "initials": "PM",
      "color": "#057642",
      "photo": null,
      "content": "Great insight!",
      "created_at": "Aug 15",
      "is_mine": false,
      "replies": [
        {
          "id": "uuid",
          "author": "Dr. Arjun Sharma",
          "initials": "AS",
          "color": "#0a66c2",
          "photo": null,
          "content": "Thank you!",
          "created_at": "Aug 15",
          "is_mine": true
        }
      ]
    }
  ]
}
```

---

### POST `/feed/posts/{id}/comments/`
Add a comment to a post.

**Auth:** Required

**Request:** `multipart/form-data`
- `content`: comment text

**Response 201:**
```json
{
  "id": "uuid",
  "author": "Dr. Arjun Sharma",
  "initials": "AS",
  "color": "#0a66c2",
  "photo": null,
  "content": "Great post!",
  "created_at": "Just now",
  "count": 6
}
```

---

### POST `/feed/comments/{id}/reply/`
Reply to a comment.

**Auth:** Required

**Request:** `multipart/form-data`
- `content`: reply text

**Response 201:**
```json
{
  "id": "uuid",
  "author": "Dr. Arjun Sharma",
  "initials": "AS",
  "color": "#0a66c2",
  "photo": null,
  "content": "Thanks for the reply!",
  "created_at": "Just now",
  "is_mine": true
}
```

---

### PATCH `/feed/comments/{id}/`
Edit own comment or reply.

**Auth:** Required

**Request:** `multipart/form-data`
- `content`: updated text

**Response 200:**
```json
{ "success": true, "content": "Updated comment" }
```

---

### DELETE `/feed/comments/{id}/`
Delete own comment or reply.

**Auth:** Required

**Response 200:**
```json
{ "success": true }
```

---

## 8. NETWORK

### POST `/network/connections/request/`
Send connection request.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{ "receiver_id": "uuid" }
```

**Response 201:**
```json
{
  "id": "uuid",
  "sender_id": "uuid",
  "receiver_id": "uuid",
  "status": "PENDING",
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

### POST `/network/connections/{id}/accept/`
Accept connection request.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{ "success": true, "message": "Connection accepted" }
```

---

### POST `/network/connections/{id}/reject/`
Reject connection request.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{ "success": true, "message": "Connection declined" }
```

---

### DELETE `/network/connections/{id}/`
Remove/withdraw connection.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{ "success": true, "message": "Connection withdrawn" }
```

---

### GET `/network/connections/`
List connections.

**Auth:** Required (DOCTOR)

**Query Params:**
- `type`: `sent` | `received` | `accepted`
- `page`, `page_size`

**Response 200:**
```json
{
  "total": 10,
  "page": 1,
  "results": [
    {
      "id": "uuid",
      "sender_id": "uuid",
      "receiver_id": "uuid",
      "status": "ACCEPTED",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

### POST `/network/follow/{user_id}/`
Follow a user or hospital.

**Auth:** Required

**Response 201:**
```json
{ "success": true, "message": "Followed" }
```

---

### DELETE `/network/follow/{user_id}/`
Unfollow a user.

**Auth:** Required

**Response 200:**
```json
{ "success": true, "message": "Unfollowed" }
```

---

### POST `/network/block/{user_id}/`
Block a user.

**Auth:** Required

**Response 201:**
```json
{ "success": true, "message": "User blocked" }
```

---

### DELETE `/network/block/{user_id}/`
Unblock a user.

**Auth:** Required

**Response 200:**
```json
{ "success": true, "message": "User unblocked" }
```

---

### GET `/network/blocked/`
List blocked users.

**Auth:** Required

**Response 200:**
```json
{ "blocked_users": ["uuid1", "uuid2"], "total": 2 }
```

---

### POST `/reports/`
Report a profile/post/comment/job/hospital.

**Auth:** Required

**Request Body:**
```json
{
  "target_type": "POST",
  "target_id": "uuid",
  "reason": "SPAM",
  "description": "This post contains spam content",
  "severity": "MEDIUM"
}
```
- `target_type`: `PROFILE` | `POST` | `COMMENT` | `JOB` | `HOSPITAL`
- `reason`: `PATIENT_PRIVACY_CONCERN` | `POTENTIAL_MEDICAL_MISINFORMATION` | `SPAM` | `HARASSMENT` | `COPYRIGHT_CONCERN` | `FAKE_DOCTOR_FALSE_CREDENTIALS` | `PROFESSIONAL_MISCONDUCT_CONCERN` | `OTHER_POLICY_VIOLATION`
- `severity`: `LOW` | `MEDIUM` | `HIGH` | `CRITICAL`

**Response 201:**
```json
{ "success": true, "message": "Report submitted successfully" }
```

---

## 9. MESSAGING

### POST `/messages/conversations/`
Start a conversation.

**Auth:** Required

**Request Body:**
```json
{ "participant_user_id": "uuid" }
```

**Response 201:**
```json
{
  "conversation_id": "uuid",
  "existing": false
}
```
> `existing: true` if conversation already exists — returns existing ID.

---

### GET `/messages/conversations/`
List my conversations.

**Auth:** Required

**Response 200:**
```json
[
  {
    "conversation_id": "uuid",
    "type": "DIRECT",
    "last_message": "Hello doctor",
    "last_message_at": "2025-01-01T00:00:00Z",
    "last_read_at": "2025-01-01T00:00:00Z"
  }
]
```

---

### GET `/messages/conversations/{id}/messages/`
Get messages in a conversation.

**Auth:** Required (must be participant)

**Query Params:** `page`, `page_size` (default 50)

**Response 200:**
```json
{
  "total": 100,
  "page": 1,
  "messages": [
    {
      "id": "uuid",
      "sender_id": "uuid",
      "content": "Hello doctor",
      "message_type": "TEXT",
      "file_id": null,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```
- `message_type`: `TEXT` | `IMAGE` | `DOCUMENT` | `SHIFT_REQUEST` | `JOB_REFERRAL`

---

### POST `/messages/conversations/{id}/messages/`
Send a message.

**Auth:** Required (must be participant)

**Request Body:**
```json
{
  "content": "Hello doctor, I have a query.",
  "message_type": "TEXT"
}
```

**Response 201:**
```json
{ "id": "uuid", "created_at": "2025-01-01T00:00:00Z" }
```

---

### POST `/messages/conversations/{id}/read/`
Mark conversation as read.

**Auth:** Required

**Response 200:**
```json
{ "success": true }
```

---

### POST `/messages/conversations/{id}/report/`
Report a conversation.

**Auth:** Required (must be participant)

**Query Params:**
- `reason`: `SPAM` | `HARASSMENT` | `PATIENT_PRIVACY_CONCERN` | `OTHER_POLICY_VIOLATION`

**Response 201:**
```json
{ "success": true, "message": "Conversation reported" }
```

---

### POST `/messages/conversations/{id}/block/`
Block a conversation.

**Auth:** Required

**Response 201:**
```json
{ "success": true, "message": "Conversation blocked" }
```

---

### DELETE `/messages/conversations/{id}/block/`
Unblock a conversation.

**Auth:** Required

**Response 200:**
```json
{ "success": true, "message": "Conversation unblocked" }
```

---

## 10. NOTIFICATIONS

### GET `/notifications/`
List notifications (paginated).

**Auth:** Required

**Query Params:** `page`, `page_size`

**Response 200:**
```json
{
  "total": 20,
  "page": 1,
  "results": [
    {
      "id": "uuid",
      "type": "CONNECTION_REQUEST",
      "title": "New connection request",
      "body": "Dr. Priya Mehta sent you a connection request",
      "is_read": false,
      "data": {},
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

### GET `/notifications/unread-count/`
Get unread notification count.

**Auth:** Required

**Response 200:**
```json
{ "unread_count": 7 }
```

---

### PATCH `/notifications/{id}/read/`
Mark notification as read.

**Auth:** Required

**Response 200:**
```json
{ "success": true }
```

---

### POST `/notifications/read-all/`
Mark all notifications as read.

**Auth:** Required

**Response 200:**
```json
{ "success": true }
```

---

### GET `/notification-preferences/`
Get per-event notification preferences.

**Auth:** Required

**Response 200:**
```json
{
  "preferences": {
    "connection_request": { "push": true, "email": false },
    "job_application": { "push": true, "email": true },
    "shift_request": { "push": true, "email": false }
  }
}
```

---

### PUT `/notification-preferences/`
Update notification preferences.

**Auth:** Required

**Request Body:**
```json
{
  "connection_request": { "push": true, "email": false },
  "job_application": { "push": false, "email": true }
}
```

**Response 200:**
```json
{ "success": true }
```

---

### POST `/devices/`
Register device for push notifications.

**Auth:** Required

**Request Body:**
```json
{
  "token": "fcm-or-apns-token",
  "platform": "ANDROID",
  "device_id": "device-uuid",
  "app_version": "1.0.0"
}
```
- `platform`: `ANDROID` | `IOS`

**Response 201:**
```json
{ "success": true, "device_id": "uuid" }
```

---

### DELETE `/devices/{id}/`
Revoke device token.

**Auth:** Required

**Response 204:** No content

---

## 11. SEARCH

### GET `/search/doctors/`
Search doctors (advanced filters).

**Auth:** Required

**Query Params:** `search`, `specialty`, `city`, `experience_min`, `page`, `page_size`

**Response 200:** Same as `/doctors/search/`

---

### GET `/search/hospitals/`
Search hospitals.

**Auth:** Required

**Query Params:** `search`, `city`, `type`, `page`, `page_size`

**Response 200:**
```json
{
  "total": 10,
  "page": 1,
  "results": [ /* hospital objects */ ]
}
```

---

### GET `/search/jobs/`
Search jobs.

**Auth:** Required

**Query Params:** `search`, `specialty`, `city`, `job_type`, `page`, `page_size`

**Response 200:** Same as `/jobs/`

---

### GET `/search/communities/`
Search specialty communities.

**Auth:** Required

**Query Params:** `search`, `page`, `page_size`

**Response 200:**
```json
{
  "total": 5,
  "results": [
    {
      "id": "uuid",
      "name": "Cardiology",
      "description": "Cardiology specialists community",
      "member_count": 250,
      "is_active": true
    }
  ]
}
```

---

### GET `/search/universal/`
Universal search across all entities.

**Auth:** Required

**Query Params:** `q` (search query), `page`, `page_size`

**Response 200:**
```json
{
  "doctors": [ /* top 3 */ ],
  "hospitals": [ /* top 3 */ ],
  "jobs": [ /* top 3 */ ],
  "communities": [ /* top 3 */ ]
}
```

---

## 12. COMMUNITIES

### GET `/communities/`
List specialty communities.

**Auth:** Required

**Query Params:** `page`, `page_size`

**Response 200:**
```json
{
  "total": 10,
  "results": [
    {
      "id": "uuid",
      "name": "Cardiology",
      "description": "Community for cardiologists",
      "member_count": 250,
      "is_active": true,
      "is_member": false
    }
  ]
}
```

---

### GET `/communities/{id}/`
Community detail.

**Auth:** Required

**Response 200:** Community object with member count and moderators

---

### POST `/communities/{id}/join/`
Join a community.

**Auth:** Required

**Response 200:**
```json
{ "success": true, "message": "Joined community" }
```

---

### DELETE `/communities/{id}/leave/`
Leave a community.

**Auth:** Required

**Response 200:**
```json
{ "success": true, "message": "Left community" }
```

---

### GET `/communities/{id}/posts/`
Get community posts.

**Auth:** Required

**Query Params:** `page`, `page_size`

**Response 200:** Same as `/feed/` response

---

### POST `/communities/{id}/posts/`
Post in a community.

**Auth:** Required (must be member)

**Request:** `multipart/form-data` — same as `/feed/posts/`

**Response 201:** Same as create post response

---

## 13. FILES

### POST `/files/upload/`
Upload a file (photo/CV/credential).

**Auth:** Required

**Request:** `multipart/form-data`
- `file`: any file
- `purpose`: `PROFILE_PHOTO` | `CV` | `CREDENTIAL` | `REPORT_EVIDENCE`

**Response 201:**
```json
{
  "id": "uuid",
  "filename": "cv.pdf",
  "content_type": "application/pdf",
  "size": 102400,
  "url": "https://..."
}
```

---

### GET `/files/{id}/`
Get file metadata.

**Auth:** Required

**Response 200:**
```json
{
  "id": "uuid",
  "filename": "cv.pdf",
  "content_type": "application/pdf",
  "size": 102400
}
```

---

### GET `/files/{id}/signed-url/`
Get expiring signed URL for file.

**Auth:** Required

**Response 200:**
```json
{
  "url": "https://s3.amazonaws.com/...",
  "expires_in": 3600
}
```

---

### DELETE `/files/{id}/`
Delete a file.

**Auth:** Required

**Response 204:** No content

---

## 14. MASTERS (Reference Data)

### GET `/masters/specialties/`
List all medical specializations.

**Auth:** Required

**Response 200:**
```json
[
  { "id": "uuid", "name": "Cardiology", "is_active": true },
  { "id": "uuid", "name": "Neurology", "is_active": true }
]
```

---

### GET `/masters/qualifications/`
List all qualifications.

**Auth:** Required

**Response 200:**
```json
[
  { "id": "uuid", "name": "MBBS", "is_active": true },
  { "id": "uuid", "name": "MD", "is_active": true }
]
```

---

### GET `/masters/job-types/`
List job types.

**Auth:** Required

**Response 200:**
```json
[
  { "value": "FULL_TIME", "label": "Full Time" },
  { "value": "PART_TIME", "label": "Part Time" },
  { "value": "LOCUM", "label": "Locum" },
  { "value": "VISITING", "label": "Visiting" },
  { "value": "CONTRACT", "label": "Contract" }
]
```

---

### GET `/masters/shift-types/`
List shift types.

**Auth:** Required

**Response 200:**
```json
[
  { "value": "DAY", "label": "Day" },
  { "value": "NIGHT", "label": "Night" },
  { "value": "ROTATIONAL", "label": "Rotational" },
  { "value": "FLEXIBLE", "label": "Flexible" }
]
```

---

## 15. SUPPORT

### POST `/support/tickets/`
Create support ticket.

**Auth:** Required

**Request Body:**
```json
{
  "subject": "Verification issue",
  "description": "My verification is stuck in pending",
  "category": "VERIFICATION"
}
```
- `category`: `GENERAL` | `VERIFICATION` | `BILLING` | `TECHNICAL`

**Response 201:**
```json
{ "id": "uuid", "status": "OPEN", "created_at": "2025-01-01T00:00:00Z" }
```

---

### GET `/support/tickets/`
List my support tickets.

**Auth:** Required

**Response 200:**
```json
{
  "total": 2,
  "results": [
    {
      "id": "uuid",
      "subject": "Verification issue",
      "category": "VERIFICATION",
      "status": "OPEN",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

### POST `/support/tickets/{id}/messages/`
Reply to support ticket.

**Auth:** Required

**Request Body:**
```json
{ "message": "I have attached my registration certificate" }
```

**Response 201:**
```json
{ "id": "uuid", "message": "...", "created_at": "2025-01-01T00:00:00Z" }
```

---

## 16. MFA (Multi-Factor Authentication)

### POST `/mfa/setup/`
Setup MFA (TOTP).

**Auth:** Required

**Response 200:**
```json
{
  "secret": "BASE32SECRET",
  "qr_code_url": "otpauth://totp/...",
  "backup_codes": ["code1", "code2"]
}
```

---

### POST `/mfa/verify/`
Verify MFA code.

**Auth:** Required

**Request Body:**
```json
{ "code": "123456" }
```

**Response 200:**
```json
{ "success": true, "mfa_enabled": true }
```

---

### DELETE `/mfa/disable/`
Disable MFA.

**Auth:** Required

**Request Body:**
```json
{ "code": "123456" }
```

**Response 200:**
```json
{ "success": true, "mfa_enabled": false }
```

---

## 17. CME (Continuing Medical Education)

### GET `/cme/events/`
List CME events.

**Auth:** Required

**Response 200:**
```json
{
  "total": 5,
  "results": [
    {
      "id": "uuid",
      "title": "Advanced Cardiac Life Support",
      "provider": "AIIMS",
      "credit_hours": 8,
      "event_date": "2025-09-15",
      "is_active": true
    }
  ]
}
```

---

### POST `/cme/credits/`
Submit CME credit.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{
  "title": "Advanced Cardiac Life Support",
  "credits": 8,
  "completion_date": "2025-09-15",
  "certificate_file_id": "uuid"
}
```

**Response 201:**
```json
{ "id": "uuid", "status": "PENDING" }
```

---

### GET `/cme/credits/`
List my CME credits.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{
  "total": 3,
  "results": [
    {
      "id": "uuid",
      "title": "Advanced Cardiac Life Support",
      "credits": 8,
      "completion_date": "2025-09-15",
      "status": "VERIFIED"
    }
  ]
}
```

---

## 18. ENDORSEMENTS

### POST `/endorsements/`
Endorse a doctor's skill.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{
  "endorsed_id": "uuid",
  "skill": "Cardiac Surgery"
}
```

**Response 201:**
```json
{ "id": "uuid", "skill": "Cardiac Surgery", "created_at": "2025-01-01T00:00:00Z" }
```

---

### GET `/endorsements/me/`
List endorsements received.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{
  "total": 5,
  "results": [
    {
      "id": "uuid",
      "endorser_name": "Dr. Priya Mehta",
      "skill": "Cardiac Surgery",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

## 19. SECOND OPINIONS

### POST `/second-opinions/`
Request a second opinion.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{
  "reviewer_id": "uuid",
  "case_summary": "Patient with complex cardiac condition...",
  "is_anonymous": true
}
```

**Response 201:**
```json
{ "id": "uuid", "status": "PENDING" }
```

---

### GET `/second-opinions/`
List my second opinion requests.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{
  "total": 2,
  "results": [
    {
      "id": "uuid",
      "reviewer_name": "Dr. Arjun Sharma",
      "status": "PENDING",
      "is_anonymous": true,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

## 20. TELEMEDICINE

### POST `/telemedicine/sessions/`
Schedule telemedicine session.

**Auth:** Required (DOCTOR)

**Request Body:**
```json
{
  "guest_doctor_id": "uuid",
  "session_type": "CONSULTATION",
  "scheduled_at": "2025-09-01T10:00:00Z",
  "duration_minutes": 30
}
```

**Response 201:**
```json
{ "id": "uuid", "status": "SCHEDULED", "join_url": "https://..." }
```

---

### GET `/telemedicine/sessions/`
List my telemedicine sessions.

**Auth:** Required (DOCTOR)

**Response 200:**
```json
{
  "total": 3,
  "results": [
    {
      "id": "uuid",
      "session_type": "CONSULTATION",
      "status": "SCHEDULED",
      "scheduled_at": "2025-09-01T10:00:00Z",
      "duration_minutes": 30
    }
  ]
}
```

---

## 21. ANALYTICS

### GET `/analytics/hospital/`
Hospital analytics snapshot.

**Auth:** Required (Hospital user)

**Response 200:**
```json
{
  "total_jobs_active": 5,
  "total_applications": 120,
  "total_hired": 8,
  "total_shifts_filled": 15,
  "snapshot_date": "2025-08-15"
}
```

---

## 22. BILLING

### GET `/billing/plans/`
List available plans.

**Auth:** Required

**Response 200:**
```json
[
  {
    "id": "uuid",
    "name": "Professional",
    "price": "4999",
    "currency": "INR",
    "billing_cycle": "MONTHLY",
    "is_active": true
  }
]
```

---

### GET `/billing/subscription/`
Get my hospital subscription.

**Auth:** Required (Hospital user)

**Response 200:**
```json
{
  "id": "uuid",
  "plan": "Professional",
  "status": "ACTIVE",
  "started_at": "2025-01-01T00:00:00Z",
  "expires_at": "2026-01-01T00:00:00Z"
}
```

---

### GET `/billing/invoices/`
List invoices.

**Auth:** Required (Hospital user)

**Response 200:**
```json
{
  "total": 3,
  "results": [
    {
      "id": "uuid",
      "amount": "4999",
      "currency": "INR",
      "status": "PAID",
      "due_date": "2025-02-01",
      "paid_at": "2025-01-28T00:00:00Z"
    }
  ]
}
```

---

## 23. HEALTH CHECK

### GET `/health` *(no /api/v1 prefix)*
Server health check.

**Auth:** Not required

**Response 200:**
```json
{ "status": "healthy", "timestamp": "2025-08-15T10:00:00Z" }
```

---

## Appendix A — Enums Reference

### User Types
| Value | Description |
|-------|-------------|
| `DOCTOR` | Doctor user |
| `HOSPITAL_ADMIN` | Hospital administrator |
| `HOSPITAL_HR` | Hospital HR/Recruiter |
| `ADMIN` | Platform admin |

### Verification Status
| Value | Description |
|-------|-------------|
| `UNVERIFIED` | Not yet submitted |
| `PENDING` | Under review |
| `VERIFIED` | Approved |
| `REJECTED` | Rejected with reason |

### Job Application Status Flow
```
APPLIED → PROFILE_VIEWED → SHORTLISTED → INTERVIEW → OFFERED → HIRED
                                                    ↘ REJECTED
(Doctor can WITHDRAW at any stage)
```

### Shift Request Status Flow
```
REQUESTED → ACCEPTED_BY_DOCTOR → CONFIRMED_BY_HOSPITAL → COMPLETED
          ↘ DECLINED_BY_DOCTOR
(Either party can CANCELLED at any stage)
```

### Report Reason Codes
| Code | Description |
|------|-------------|
| `PATIENT_PRIVACY_CONCERN` | Patient data exposed |
| `POTENTIAL_MEDICAL_MISINFORMATION` | False medical info |
| `SPAM` | Spam content |
| `HARASSMENT` | Harassment |
| `COPYRIGHT_CONCERN` | Copyright violation |
| `FAKE_DOCTOR_FALSE_CREDENTIALS` | Fake credentials |
| `PROFESSIONAL_MISCONDUCT_CONCERN` | Misconduct |
| `OTHER_POLICY_VIOLATION` | Other violation |

---

## Appendix B — Quick Start for Mobile

### Step 1 — Register & Login
```
POST /api/v1/auth/register/   → get tokens
POST /api/v1/auth/login/      → get tokens
```

### Step 2 — Load Home Screen (1 API call)
```
GET /api/v1/feed/home/   → stats + urgent jobs + suggested doctors + unread counts
```

### Step 3 — Load Feed
```
GET /api/v1/feed/?page=1
```

### Step 4 — Doctor Profile Setup
```
POST /api/v1/doctors/profile/me/registrations/   → add NMC registration
POST /api/v1/doctors/profile/me/verification/submit/   → submit for verification
```

### Step 5 — Apply to Job
```
GET  /api/v1/jobs/?specialty=uuid   → browse jobs
POST /api/v1/jobs/{id}/apply/       → one-tap apply
```

### Step 6 — Post Availability (Locum)
```
POST /api/v1/availability/   → post availability with slots
GET  /api/v1/shifts/requirements/?urgency=IMMEDIATE   → browse urgent shifts
POST /api/v1/shifts/requirements/{id}/request/        → request shift
```

### Token Refresh Flow
```
Access token expires → POST /api/v1/auth/refresh/ with refresh_token → new access_token
```

### Swagger UI
```
http://3.111.58.158/api/docs
```
