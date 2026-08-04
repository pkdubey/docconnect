"""
Centralized Pydantic schemas for DocConnect API.
Routers import from here for shared types.
"""
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# ── Enums ─────────────────────────────────────────────────────

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


class AvailabilityType(str, Enum):
    LOCUM = "LOCUM"
    VISITING = "VISITING"
    TEMPORARY = "TEMPORARY"
    PART_TIME = "PART_TIME"


class HospitalType(str, Enum):
    HOSPITAL = "HOSPITAL"
    CLINIC = "CLINIC"
    NURSING_HOME = "NURSING_HOME"
    MEDICAL_COLLEGE = "MEDICAL_COLLEGE"


class HospitalAdminRole(str, Enum):
    ADMIN = "ADMIN"
    HR = "HR"
    RECRUITER = "RECRUITER"


# ── Shared ────────────────────────────────────────────────────

class Location(BaseModel):
    address: Optional[str] = None
    city: str
    state: str
    pincode: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None


# ── Auth ──────────────────────────────────────────────────────

class OTPRequest(BaseModel):
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    purpose: str = Field(..., pattern=r'^(LOGIN|REGISTER|RESET_PASSWORD)$')


class OTPVerify(BaseModel):
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    otp: str = Field(..., min_length=6, max_length=6)
    purpose: str = Field(default='LOGIN')
    device_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── Doctor ────────────────────────────────────────────────────

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
    professional_location: Optional[dict]
    experience_years: float
    open_to_opportunities: bool
    verification_status: VerificationStatus
    is_verified: bool
    created_at: datetime
    updated_at: datetime


# ── Job ───────────────────────────────────────────────────────

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


# ── Hospital ──────────────────────────────────────────────────

class HospitalRegisterRequest(BaseModel):
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    email: EmailStr
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
    type: str
    about: Optional[str]
    location: dict
    bed_count: Optional[int]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    verification_status: str
    created_at: datetime


# ── Availability ──────────────────────────────────────────────

class SlotCreate(BaseModel):
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
    slots: List[SlotCreate]


# ── Shift ─────────────────────────────────────────────────────

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
    urgency: str = Field("NORMAL", pattern=r'^(NORMAL|URGENT|IMMEDIATE)$')
    notes: Optional[str] = None
    branch_id: Optional[str] = None
