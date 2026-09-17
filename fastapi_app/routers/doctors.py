from datetime import date
from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from fastapi_app.dependencies import get_current_doctor, get_current_user

router = APIRouter(prefix="/api/v1/doctors", tags=["Doctors"])


# ── Request Schemas ───────────────────────────────────────────

class Location(BaseModel):
    address: Optional[str] = None
    city: str
    state: str
    pincode: Optional[str] = None
    coordinates: Optional[Dict[str, Any]] = None


class DoctorProfileCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=80)
    last_name: str = Field(..., min_length=1, max_length=80)
    headline: Optional[str] = Field(None, max_length=160)
    about: Optional[str] = None
    primary_specialization_id: Optional[str] = None
    clinical_interests: Optional[List[str]] = []
    professional_location: Optional[Location] = None
    experience_years: Optional[float] = Field(0, ge=0, le=60)


class DoctorProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=80)
    last_name: Optional[str] = Field(None, min_length=1, max_length=80)
    headline: Optional[str] = Field(None, max_length=160)
    about: Optional[str] = None
    primary_specialization_id: Optional[str] = None
    clinical_interests: Optional[List[str]] = None
    professional_location: Optional[Location] = None
    experience_years: Optional[float] = Field(None, ge=0, le=60)
    open_to_opportunities: Optional[bool] = None


class DoctorRegistrationCreate(BaseModel):
    council_id: str
    registration_number: str
    registration_year: int = Field(..., ge=1950, le=2100)
    is_primary: bool = True


class DoctorQualificationCreate(BaseModel):
    degree: str = Field(..., max_length=100)
    institution: str = Field(..., max_length=255)
    year: int = Field(..., ge=1950, le=2100)
    specialization: Optional[str] = Field(None, max_length=100)


class DoctorExperienceCreate(BaseModel):
    role: str = Field(..., max_length=100)
    hospital_name: str = Field(..., max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None


# ── Response Schemas ──────────────────────────────────────────

class DoctorProfileOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "550e8400-e29b-41d4-a716-446655440001",
        "first_name": "Arjun", "last_name": "Sharma", "full_name": "Arjun Sharma",
        "photo_file_id": None, "headline": "Cardiologist · AIIMS Delhi · 12 yrs",
        "about": "Senior cardiologist with 12 years experience.",
        "primary_specialization_id": "550e8400-e29b-41d4-a716-446655440002",
        "clinical_interests": [], "professional_location": {"city": "Mumbai", "state": "Maharashtra"},
        "experience_years": 12.0, "open_to_opportunities": True,
        "verification_status": "VERIFIED", "is_verified": True,
        "created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-01T00:00:00Z"
    }})
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
    professional_location: Optional[Dict[str, Any]]
    experience_years: float
    open_to_opportunities: bool
    verification_status: str
    is_verified: bool
    created_at: str
    updated_at: str


class DoctorSearchResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "total": 1, "page": 1, "page_size": 20, "results": []
    }})
    total: int
    page: int
    page_size: int
    results: List[DoctorProfileOut]


class RegistrationOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "council_id": "550e8400-e29b-41d4-a716-446655440001",
        "registration_number": "MH-12345", "registration_year": 2010,
        "is_primary": True, "verification_status": "PENDING"
    }})
    id: str
    council_id: str
    registration_number: str
    registration_year: int
    is_primary: bool
    verification_status: str


class RegistrationCreateOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "registration_number": "MH-12345", "verification_status": "PENDING"
    }})
    id: str
    registration_number: str
    verification_status: str


class QualificationOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "degree": "MBBS", "institution": "AIIMS Delhi", "year": 2010, "specialization": "Cardiology"
    }})
    id: str
    degree: str
    institution: str
    year: int
    specialization: Optional[str]


class ExperienceOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "role": "Senior Cardiologist", "hospital_name": "Apollo Hospital",
        "location": "Mumbai", "start_date": "2015-01-01", "end_date": None, "is_current": True
    }})
    id: str
    role: str
    hospital_name: str
    location: Optional[str]
    start_date: str
    end_date: Optional[str]
    is_current: bool


class PhotoUploadOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "success": True, "file_id": "550e8400-e29b-41d4-a716-446655440000"
    }})
    success: bool
    file_id: str


# ── Helper ────────────────────────────────────────────────────

def _profile_dict(dp) -> DoctorProfileOut:
    return DoctorProfileOut(
        id=str(dp.id),
        user_id=str(dp.user_id),
        first_name=dp.first_name,
        last_name=dp.last_name,
        full_name=dp.full_name,
        photo_file_id=str(dp.photo_file_id) if dp.photo_file_id else None,
        headline=dp.headline,
        about=dp.about,
        primary_specialization_id=str(dp.primary_specialization_id) if dp.primary_specialization_id else None,
        clinical_interests=[str(i) for i in (dp.clinical_interests or [])],
        professional_location=dp.professional_location or None,
        experience_years=float(dp.experience_years),
        open_to_opportunities=dp.open_to_opportunities,
        verification_status=dp.verification_status,
        is_verified=dp.is_verified,
        created_at=dp.created_at.isoformat(),
        updated_at=dp.updated_at.isoformat(),
    )


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/profile/", response_model=DoctorProfileOut, status_code=201, summary="Create doctor profile")
async def create_doctor_profile(profile: DoctorProfileCreate, current_user=Depends(get_current_user)):
    from apps.doctors.models import DoctorProfile
    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Not a doctor")

    def _create():
        if DoctorProfile.objects.filter(user=current_user).exists():
            raise HTTPException(status_code=409, detail="Profile already exists")
        return DoctorProfile.objects.create(
            user=current_user,
            first_name=profile.first_name,
            last_name=profile.last_name,
            headline=profile.headline,
            about=profile.about,
            primary_specialization_id=profile.primary_specialization_id,
            clinical_interests=profile.clinical_interests or [],
            professional_location=profile.professional_location.model_dump() if profile.professional_location else {},
            experience_years=profile.experience_years or 0,
        )

    try:
        dp = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return _profile_dict(dp)


@router.get("/profile/me/", response_model=DoctorProfileOut, summary="Get my profile")
async def get_my_profile(current_doctor=Depends(get_current_doctor)):
    return _profile_dict(current_doctor)


@router.patch("/profile/me/", response_model=DoctorProfileOut, summary="Update my profile")
async def update_my_profile(update: DoctorProfileUpdate, current_doctor=Depends(get_current_doctor)):
    def _update():
        data = update.model_dump(exclude_none=True)
        if 'professional_location' in data and data['professional_location']:
            data['professional_location'] = update.professional_location.model_dump()
        for field, value in data.items():
            setattr(current_doctor, field, value)
        current_doctor.save()
        return current_doctor

    dp = await sync_to_async(_update, thread_sensitive=True)()
    return _profile_dict(dp)


@router.get("/search/", response_model=DoctorSearchResponse, summary="Search doctors")
async def search_doctors(
    search: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    experience_min: Optional[float] = Query(None),
    open_to_opportunities: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.doctors.models import DoctorProfile
    from django.db.models import Q

    def _search():
        qs = DoctorProfile.objects.filter(verification_status='VERIFIED')
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(headline__icontains=search)
            )
        if specialty:
            qs = qs.filter(primary_specialization_id=specialty)
        if city:
            qs = qs.filter(professional_location__city__icontains=city)
        if experience_min is not None:
            qs = qs.filter(experience_years__gte=experience_min)
        if open_to_opportunities is not None:
            qs = qs.filter(open_to_opportunities=open_to_opportunities)
        total = qs.count()
        results = list(qs[(page - 1) * page_size: page * page_size])
        return total, results

    total, results = await sync_to_async(_search, thread_sensitive=True)()
    return DoctorSearchResponse(total=total, page=page, page_size=page_size, results=[_profile_dict(d) for d in results])


@router.get("/profile/me/registrations/", response_model=List[RegistrationOut], summary="List my registrations")
async def list_registrations(current_doctor=Depends(get_current_doctor)):
    regs = await sync_to_async(lambda: list(current_doctor.registrations.all()), thread_sensitive=True)()
    return [RegistrationOut(id=str(r.id), council_id=str(r.council_id),
                            registration_number=r.registration_number, registration_year=r.registration_year,
                            is_primary=r.is_primary, verification_status=r.verification_status) for r in regs]


@router.post("/profile/me/registrations/", response_model=RegistrationCreateOut, status_code=201, summary="Add registration")
async def add_registration(reg: DoctorRegistrationCreate, current_doctor=Depends(get_current_doctor)):
    from apps.doctors.models import DoctorRegistration

    def _create():
        if DoctorRegistration.objects.filter(council_id=reg.council_id, registration_number=reg.registration_number).exists():
            raise HTTPException(status_code=409, detail="Registration already exists")
        return DoctorRegistration.objects.create(
            doctor=current_doctor, council_id=reg.council_id,
            registration_number=reg.registration_number,
            registration_year=reg.registration_year, is_primary=reg.is_primary,
        )

    try:
        r = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return RegistrationCreateOut(id=str(r.id), registration_number=r.registration_number, verification_status=r.verification_status)


@router.get("/profile/me/qualifications/", response_model=List[QualificationOut], summary="List qualifications")
async def list_qualifications(current_doctor=Depends(get_current_doctor)):
    quals = await sync_to_async(lambda: list(current_doctor.qualifications.all()), thread_sensitive=True)()
    return [QualificationOut(id=str(q.id), degree=q.degree, institution=q.institution,
                             year=q.year, specialization=q.specialization) for q in quals]


@router.post("/profile/me/qualifications/", response_model=QualificationOut, status_code=201, summary="Add qualification")
async def add_qualification(qual: DoctorQualificationCreate, current_doctor=Depends(get_current_doctor)):
    from apps.doctors.models import DoctorQualification

    q = await sync_to_async(lambda: DoctorQualification.objects.create(
        doctor=current_doctor, degree=qual.degree, institution=qual.institution,
        year=qual.year, specialization=qual.specialization,
    ), thread_sensitive=True)()
    return QualificationOut(id=str(q.id), degree=q.degree, institution=q.institution,
                            year=q.year, specialization=q.specialization)


@router.delete("/profile/me/qualifications/{qual_id}/", status_code=204, summary="Delete qualification")
async def delete_qualification(qual_id: str, current_doctor=Depends(get_current_doctor)):
    from apps.doctors.models import DoctorQualification
    deleted = await sync_to_async(
        lambda: DoctorQualification.objects.filter(id=qual_id, doctor=current_doctor).delete()[0],
        thread_sensitive=True,
    )()
    if not deleted:
        raise HTTPException(status_code=404, detail="Qualification not found")


@router.get("/profile/me/experiences/", response_model=List[ExperienceOut], summary="List experiences")
async def list_experiences(current_doctor=Depends(get_current_doctor)):
    exps = await sync_to_async(lambda: list(current_doctor.experiences.order_by('-start_date')), thread_sensitive=True)()
    return [ExperienceOut(id=str(e.id), role=e.role, hospital_name=e.hospital_name,
                          location=e.location, start_date=str(e.start_date),
                          end_date=str(e.end_date) if e.end_date else None, is_current=e.is_current) for e in exps]


@router.post("/profile/me/experiences/", response_model=ExperienceOut, status_code=201, summary="Add experience")
async def add_experience(exp: DoctorExperienceCreate, current_doctor=Depends(get_current_doctor)):
    from apps.doctors.models import DoctorExperience

    e = await sync_to_async(lambda: DoctorExperience.objects.create(
        doctor=current_doctor, role=exp.role, hospital_name=exp.hospital_name,
        location=exp.location, start_date=exp.start_date, end_date=exp.end_date,
        is_current=exp.is_current, description=exp.description,
    ), thread_sensitive=True)()
    return ExperienceOut(id=str(e.id), role=e.role, hospital_name=e.hospital_name,
                         location=e.location, start_date=str(e.start_date),
                         end_date=str(e.end_date) if e.end_date else None, is_current=e.is_current)


@router.delete("/profile/me/experiences/{exp_id}/", status_code=204, summary="Delete experience")
async def delete_experience(exp_id: str, current_doctor=Depends(get_current_doctor)):
    from apps.doctors.models import DoctorExperience
    deleted = await sync_to_async(
        lambda: DoctorExperience.objects.filter(id=exp_id, doctor=current_doctor).delete()[0],
        thread_sensitive=True,
    )()
    if not deleted:
        raise HTTPException(status_code=404, detail="Experience not found")


@router.get("/profile/{doctor_id}/", response_model=DoctorProfileOut, summary="Get doctor profile by ID")
async def get_doctor_profile(doctor_id: str, current_user=Depends(get_current_user)):
    from apps.doctors.models import DoctorProfile

    def _get():
        try:
            return DoctorProfile.objects.get(id=doctor_id)
        except DoctorProfile.DoesNotExist:
            return None

    dp = await sync_to_async(_get, thread_sensitive=True)()
    if dp is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if dp.profile_visibility == 'CONNECTIONS_ONLY':
        raise HTTPException(status_code=403, detail="Profile is private")
    if dp.profile_visibility == 'DOCTORS_ONLY' and current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Doctors only")
    return _profile_dict(dp)


@router.post("/profile/me/photo/", response_model=PhotoUploadOut, summary="Upload profile photo")
async def upload_photo(file: UploadFile = File(...), current_doctor=Depends(get_current_doctor)):
    from apps.core.services.storage import upload_file_to_s3
    if file.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
        raise HTTPException(status_code=400, detail="Only JPEG/PNG/WEBP allowed")
    file_id = await upload_file_to_s3(file, folder="doctor-photos")

    await sync_to_async(lambda: (
        setattr(current_doctor, 'photo_file_id', file_id),
        current_doctor.save(update_fields=['photo_file_id'])
    ), thread_sensitive=True)()
    return PhotoUploadOut(success=True, file_id=str(file_id))
