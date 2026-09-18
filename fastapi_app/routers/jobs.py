from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from fastapi_app.dependencies import get_current_doctor, get_current_user

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


# ── Request Schemas ───────────────────────────────────────────

class Location(BaseModel):
    address: Optional[str] = None
    city: str
    state: str
    pincode: Optional[str] = None
    coordinates: Optional[Dict[str, Any]] = None


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
    closing_date: Optional[datetime] = None


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r'^(PROFILE_VIEWED|SHORTLISTED|INTERVIEW|OFFERED|HIRED|REJECTED)$')
    notes: Optional[str] = None


# ── Response Schemas ──────────────────────────────────────────

class JobCreateOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000", "title": "Senior Cardiologist",
        "status": "PUBLISHED", "created_at": "2025-01-01T00:00:00Z"
    }})
    id: str
    title: str
    status: str
    created_at: str


class JobListItem(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000", "title": "Senior Cardiologist",
        "hospital_name": "Apollo Hospital", "job_type": "FULL_TIME",
        "location": {"city": "Mumbai", "state": "Maharashtra"}, "is_urgent": False,
        "salary_min": "150000", "salary_max": "250000", "salary_visibility": "PUBLIC",
        "published_at": "2025-01-01T00:00:00Z",
        "match_score": 85, "match_factors": ["Specialization match", "Experience match"]
    }})
    id: str
    title: str
    hospital_name: str
    job_type: str
    location: Dict[str, Any]
    is_urgent: bool
    salary_min: Optional[str]
    salary_max: Optional[str]
    salary_visibility: str
    published_at: Optional[str]
    match_score: Optional[int] = None
    match_factors: Optional[List[str]] = None


class JobListResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "total": 1, "page": 1, "page_size": 20, "results": []
    }})
    total: int
    page: int
    page_size: int
    results: List[JobListItem]


class JobDetailOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000", "title": "Senior Cardiologist",
        "hospital_id": "550e8400-e29b-41d4-a716-446655440001", "hospital_name": "Apollo Hospital",
        "description": "Looking for a senior cardiologist.", "responsibilities": None, "requirements": None,
        "location": {"city": "Mumbai", "state": "Maharashtra"}, "job_type": "FULL_TIME",
        "shift_type": "DAY", "experience_min_years": 5.0, "experience_max_years": None,
        "salary_min": "150000", "salary_max": "250000", "salary_visibility": "PUBLIC",
        "positions": 1, "is_urgent": False, "closing_date": None
    }})
    id: str
    title: str
    hospital_id: str
    hospital_name: str
    description: str
    responsibilities: Optional[str]
    requirements: Optional[str]
    location: Dict[str, Any]
    job_type: str
    shift_type: str
    experience_min_years: float
    experience_max_years: Optional[float]
    salary_min: Optional[str]
    salary_max: Optional[str]
    salary_visibility: str
    positions: int
    is_urgent: bool
    closing_date: Optional[str]


class ApplyOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "success": True, "application_id": "550e8400-e29b-41d4-a716-446655440000", "status": "APPLIED"
    }})
    success: bool
    application_id: str
    status: str


class WithdrawOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"success": True, "status": "WITHDRAWN"}})
    success: bool
    status: str


class ApplicationItem(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "application_id": "550e8400-e29b-41d4-a716-446655440000",
        "job_id": "550e8400-e29b-41d4-a716-446655440001",
        "job_title": "Senior Cardiologist", "hospital_name": "Apollo Hospital",
        "status": "APPLIED", "applied_at": "2025-01-01T00:00:00Z"
    }})
    application_id: str
    job_id: str
    job_title: str
    hospital_name: str
    status: str
    applied_at: str


class MyApplicationsResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"total": 1, "page": 1, "results": []}})
    total: int
    page: int
    results: List[ApplicationItem]


class ApplicantItem(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "application_id": "550e8400-e29b-41d4-a716-446655440000",
        "doctor_id": "550e8400-e29b-41d4-a716-446655440001",
        "doctor_name": "Arjun Sharma", "status": "APPLIED", "applied_at": "2025-01-01T00:00:00Z"
    }})
    application_id: str
    doctor_id: str
    doctor_name: str
    status: str
    applied_at: str


class ApplicantsResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"total": 1, "page": 1, "results": []}})
    total: int
    page: int
    results: List[ApplicantItem]


class ApplicationStatusOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "success": True, "application_id": "550e8400-e29b-41d4-a716-446655440000", "status": "SHORTLISTED"
    }})
    success: bool
    application_id: str
    status: str


# ── Match Score Helper ───────────────────────────────────────

def _compute_match(job, doctor) -> tuple:
    """Return (score 0-100, factors list) for a job vs doctor."""
    if doctor is None:
        return None, None
    score = 0
    factors = []
    if job.specialty_id and str(job.specialty_id) == str(doctor.primary_specialization_id or ''):
        score += 40
        factors.append("Specialization match")
    exp = float(doctor.experience_years or 0)
    req = float(job.experience_min_years or 0)
    if exp >= req:
        score += 30
        factors.append("Experience match")
    elif exp >= req * 0.8:
        score += 15
        factors.append("Near experience match")
    if doctor.open_to_opportunities:
        score += 15
        factors.append("Open to opportunities")
    if doctor.verification_status == 'VERIFIED':
        score += 15
        factors.append("Verified doctor")
    return min(score, 100), factors


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/", response_model=JobCreateOut, status_code=201, summary="Create a job posting")
async def create_job(job: JobCreate, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobPost

    def _create():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        jp = JobPost.objects.create(
            hospital=hu.hospital, branch=hu.branch,
            title=job.title, specialty_id=job.specialty_id,
            qualification_ids=job.qualification_ids, description=job.description,
            responsibilities=job.responsibilities, requirements=job.requirements,
            location=job.location.model_dump(), salary_min=job.salary_min,
            salary_max=job.salary_max, salary_visibility=job.salary_visibility.value,
            currency=job.currency, job_type=job.job_type.value,
            experience_min_years=job.experience_min_years,
            experience_max_years=job.experience_max_years,
            shift_type=job.shift_type, joining_requirement=job.joining_requirement,
            positions=job.positions, is_urgent=job.is_urgent,
            status='PUBLISHED', posted_by=current_user,
            published_at=datetime.now(), closing_date=job.closing_date,
        )
        return jp

    try:
        jp = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return JobCreateOut(id=str(jp.id), title=jp.title, status=jp.status, created_at=jp.created_at.isoformat())


@router.get("/my-applications/", response_model=MyApplicationsResponse, summary="Doctor's job applications")
async def my_applications(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_doctor=Depends(get_current_doctor),
):
    from apps.jobs.models import JobApplication

    def _list():
        qs = JobApplication.objects.filter(doctor=current_doctor).select_related('job', 'job__hospital')
        if status:
            qs = qs.filter(status=status)
        total = qs.count()
        results = list(qs.order_by('-applied_at')[(page - 1) * page_size: page * page_size])
        return total, results

    total, results = await sync_to_async(_list, thread_sensitive=True)()
    return MyApplicationsResponse(
        total=total, page=page,
        results=[ApplicationItem(
            application_id=str(a.id), job_id=str(a.job_id),
            job_title=a.job.title, hospital_name=a.job.hospital.name,
            status=a.status, applied_at=a.applied_at.isoformat(),
        ) for a in results],
    )


@router.get("/", response_model=JobListResponse, summary="List published jobs")
async def list_jobs(
    specialty: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_urgent: Optional[bool] = Query(None),
    experience_max: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.jobs.models import JobPost

    def _list():
        qs = JobPost.objects.filter(status='PUBLISHED').select_related('hospital')
        if specialty:
            qs = qs.filter(specialty_id=specialty)
        if city:
            qs = qs.filter(location__city__icontains=city)
        if job_type:
            qs = qs.filter(job_type=job_type)
        if is_urgent is not None:
            qs = qs.filter(is_urgent=is_urgent)
        if experience_max is not None:
            qs = qs.filter(experience_min_years__lte=experience_max)
        if search:
            from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
            qs = qs.annotate(
                rank=SearchRank(SearchVector('title', 'description'), SearchQuery(search))
            ).filter(rank__gte=0.1).order_by('-rank')
        total = qs.count()
        results = list(qs[(page - 1) * page_size: page * page_size])
        # Fetch doctor profile for match scoring
        doctor = None
        if current_user.user_type == 'DOCTOR':
            try:
                doctor = current_user.doctor_profile
            except Exception:
                pass
        return total, results, doctor

    total, results, doctor = await sync_to_async(_list, thread_sensitive=True)()
    items = []
    for j in results:
        score, factors = _compute_match(j, doctor)
        items.append(JobListItem(
            id=str(j.id), title=j.title, hospital_name=j.hospital.name,
            job_type=j.job_type, location=j.location or {}, is_urgent=j.is_urgent,
            salary_min=str(j.salary_min) if j.salary_min else None,
            salary_max=str(j.salary_max) if j.salary_max else None,
            salary_visibility=j.salary_visibility,
            published_at=j.published_at.isoformat() if j.published_at else None,
            match_score=score,
            match_factors=factors,
        ))
    return JobListResponse(total=total, page=page, page_size=page_size, results=items)


@router.get("/{job_id}/", response_model=JobDetailOut, summary="Get job details")
async def get_job(job_id: str, current_user=Depends(get_current_user)):
    from apps.jobs.models import JobPost

    def _get():
        try:
            return JobPost.objects.select_related('hospital').get(id=job_id, status='PUBLISHED')
        except JobPost.DoesNotExist:
            return None

    j = await sync_to_async(_get, thread_sensitive=True)()
    if j is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobDetailOut(
        id=str(j.id), title=j.title, hospital_id=str(j.hospital_id),
        hospital_name=j.hospital.name, description=j.description,
        responsibilities=j.responsibilities, requirements=j.requirements,
        location=j.location or {}, job_type=j.job_type, shift_type=j.shift_type,
        experience_min_years=float(j.experience_min_years),
        experience_max_years=float(j.experience_max_years) if j.experience_max_years else None,
        salary_min=str(j.salary_min) if j.salary_min else None,
        salary_max=str(j.salary_max) if j.salary_max else None,
        salary_visibility=j.salary_visibility, positions=j.positions,
        is_urgent=j.is_urgent,
        closing_date=j.closing_date.isoformat() if j.closing_date else None,
    )


@router.post("/{job_id}/apply/", response_model=ApplyOut, status_code=201, summary="Apply to a job")
async def apply_to_job(job_id: str, cv_file_id: Optional[str] = None, current_doctor=Depends(get_current_doctor)):
    from apps.jobs.models import JobApplication, JobPost

    def _apply():
        try:
            job = JobPost.objects.get(id=job_id, status='PUBLISHED')
        except JobPost.DoesNotExist:
            raise HTTPException(status_code=404, detail="Job not found")
        if JobApplication.objects.filter(job=job, doctor=current_doctor).exists():
            raise HTTPException(status_code=409, detail="Already applied")
        return JobApplication.objects.create(job=job, doctor=current_doctor, cv_file_id=cv_file_id)

    try:
        app_obj = await sync_to_async(_apply, thread_sensitive=True)()
    except HTTPException:
        raise
    return ApplyOut(success=True, application_id=str(app_obj.id), status=app_obj.status)


@router.post("/{job_id}/withdraw/", response_model=WithdrawOut, summary="Withdraw job application")
async def withdraw_application(job_id: str, current_doctor=Depends(get_current_doctor)):
    from apps.jobs.models import JobApplication

    def _withdraw():
        try:
            app_obj = JobApplication.objects.get(job_id=job_id, doctor=current_doctor)
        except JobApplication.DoesNotExist:
            raise HTTPException(status_code=404, detail="Application not found")
        if app_obj.status in ('HIRED', 'REJECTED', 'WITHDRAWN'):
            raise HTTPException(status_code=400, detail=f"Cannot withdraw from status: {app_obj.status}")
        app_obj.status = 'WITHDRAWN'
        app_obj.save(update_fields=['status', 'updated_at'])

    try:
        await sync_to_async(_withdraw, thread_sensitive=True)()
    except HTTPException:
        raise
    return WithdrawOut(success=True, status="WITHDRAWN")


@router.get("/{job_id}/applications/", response_model=ApplicantsResponse, summary="List applicants for a job")
async def list_job_applications(
    job_id: str,
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobApplication, JobPost

    def _list():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            job = JobPost.objects.get(id=job_id, hospital=hu.hospital)
        except JobPost.DoesNotExist:
            raise HTTPException(status_code=404, detail="Job not found")
        qs = JobApplication.objects.filter(job=job).select_related('doctor')
        if status:
            qs = qs.filter(status=status)
        total = qs.count()
        results = list(qs.order_by('-applied_at')[(page - 1) * page_size: page * page_size])
        return total, results

    try:
        total, results = await sync_to_async(_list, thread_sensitive=True)()
    except HTTPException:
        raise
    return ApplicantsResponse(
        total=total, page=page,
        results=[ApplicantItem(
            application_id=str(a.id), doctor_id=str(a.doctor_id),
            doctor_name=a.doctor.full_name, status=a.status,
            applied_at=a.applied_at.isoformat(),
        ) for a in results],
    )


@router.patch("/applications/{application_id}/status/", response_model=ApplicationStatusOut, summary="Update application status")
async def update_application_status(
    application_id: str,
    body: ApplicationStatusUpdate,
    current_user=Depends(get_current_user),
):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import ApplicationHistory, JobApplication

    def _update():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            app_obj = JobApplication.objects.select_related('job').get(
                id=application_id, job__hospital=hu.hospital
            )
        except JobApplication.DoesNotExist:
            raise HTTPException(status_code=404, detail="Application not found")
        old_status = app_obj.status
        app_obj.status = body.status
        app_obj.save(update_fields=['status', 'updated_at'])
        ApplicationHistory.objects.create(
            application=app_obj, from_status=old_status,
            to_status=body.status, changed_by=current_user, notes=body.notes,
        )

    try:
        await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return ApplicationStatusOut(success=True, application_id=application_id, status=body.status)


# ── Save / Unsave Job ─────────────────────────────────────────

@router.post("/{job_id}/save/", status_code=201, summary="Save a job")
async def save_job(job_id: str, current_doctor=Depends(get_current_doctor)):
    def _save():
        saved = current_doctor.metadata.get('saved_jobs', [])
        if job_id not in saved:
            saved.append(job_id)
            current_doctor.metadata['saved_jobs'] = saved
            current_doctor.save(update_fields=['metadata'])

    await sync_to_async(_save, thread_sensitive=True)()
    return {"success": True, "message": "Job saved"}


@router.delete("/{job_id}/save/", summary="Unsave a job")
async def unsave_job(job_id: str, current_doctor=Depends(get_current_doctor)):
    def _unsave():
        saved = current_doctor.metadata.get('saved_jobs', [])
        if job_id in saved:
            saved.remove(job_id)
            current_doctor.metadata['saved_jobs'] = saved
            current_doctor.save(update_fields=['metadata'])

    await sync_to_async(_unsave, thread_sensitive=True)()
    return {"success": True, "message": "Job unsaved"}


@router.post("/{job_id}/publish/", summary="Publish a draft job")
async def publish_job(job_id: str, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobPost

    def _publish():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            job = JobPost.objects.get(id=job_id, hospital=hu.hospital, status='DRAFT')
        except JobPost.DoesNotExist:
            raise HTTPException(status_code=404, detail="Draft job not found")
        job.status = 'PUBLISHED'
        job.published_at = datetime.now()
        job.save(update_fields=['status', 'published_at'])

    try:
        await sync_to_async(_publish, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "status": "PUBLISHED"}


@router.post("/{job_id}/close/", summary="Close a job posting")
async def close_job(job_id: str, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobPost

    def _close():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        updated = JobPost.objects.filter(id=job_id, hospital=hu.hospital).update(status='CLOSED')
        if not updated:
            raise HTTPException(status_code=404, detail="Job not found")

    try:
        await sync_to_async(_close, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "status": "CLOSED"}


class InterviewCreate(BaseModel):
    scheduled_at: datetime
    mode: str = "IN_PERSON"  # IN_PERSON / VIDEO / PHONE
    notes: Optional[str] = None


class OfferCreate(BaseModel):
    salary: Optional[str] = None
    joining_date: Optional[str] = None
    notes: Optional[str] = None


class NoteCreate(BaseModel):
    note: str


@router.post("/applications/{application_id}/interview/", status_code=201, summary="Schedule interview")
async def schedule_interview(application_id: str, body: InterviewCreate, current_user=Depends(get_current_user)):
    import uuid
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobApplication

    def _schedule():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            app_obj = JobApplication.objects.select_related('job').get(
                id=application_id, job__hospital=hu.hospital
            )
        except JobApplication.DoesNotExist:
            raise HTTPException(status_code=404, detail="Application not found")
        interviews = app_obj.metadata.get('interviews', [])
        interview = {
            "id": str(uuid.uuid4()),
            "scheduled_at": body.scheduled_at.isoformat(),
            "mode": body.mode,
            "notes": body.notes,
            "outcome": None,
        }
        interviews.append(interview)
        app_obj.metadata['interviews'] = interviews
        app_obj.status = 'INTERVIEW'
        app_obj.save(update_fields=['metadata', 'status', 'updated_at'])
        return interview

    try:
        interview = await sync_to_async(_schedule, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "interview_id": interview['id'], "scheduled_at": interview['scheduled_at']}


@router.patch("/applications/{application_id}/interview/{interview_id}/", status_code=200, summary="Update interview outcome")
async def update_interview_outcome(
    application_id: str,
    interview_id: str,
    outcome: str,
    notes: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobApplication

    def _update():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            app_obj = JobApplication.objects.select_related('job').get(
                id=application_id, job__hospital=hu.hospital
            )
        except JobApplication.DoesNotExist:
            raise HTTPException(status_code=404, detail="Application not found")
        interviews = app_obj.metadata.get('interviews', [])
        for iv in interviews:
            if iv['id'] == interview_id:
                iv['outcome'] = outcome
                if notes:
                    iv['outcome_notes'] = notes
                app_obj.metadata['interviews'] = interviews
                app_obj.save(update_fields=['metadata'])
                return iv
        raise HTTPException(status_code=404, detail="Interview not found")

    try:
        iv = await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "interview_id": iv['id'], "outcome": iv['outcome']}


@router.post("/applications/{application_id}/offer/", status_code=201, summary="Send offer")
async def send_offer(application_id: str, body: OfferCreate, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import ApplicationHistory, JobApplication

    def _offer():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            app_obj = JobApplication.objects.select_related('job').get(
                id=application_id, job__hospital=hu.hospital
            )
        except JobApplication.DoesNotExist:
            raise HTTPException(status_code=404, detail="Application not found")
        old_status = app_obj.status
        app_obj.metadata['offer'] = {
            "salary": body.salary, "joining_date": body.joining_date, "notes": body.notes
        }
        app_obj.status = 'OFFERED'
        app_obj.save(update_fields=['metadata', 'status', 'updated_at'])
        ApplicationHistory.objects.create(
            application=app_obj, from_status=old_status,
            to_status='OFFERED', changed_by=current_user, notes=body.notes,
        )

    try:
        await sync_to_async(_offer, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "status": "OFFERED"}


@router.post("/applications/{application_id}/notes/", status_code=201, summary="Add internal note")
async def add_application_note(application_id: str, body: NoteCreate, current_user=Depends(get_current_user)):
    import uuid
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobApplication

    def _add_note():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            app_obj = JobApplication.objects.select_related('job').get(
                id=application_id, job__hospital=hu.hospital
            )
        except JobApplication.DoesNotExist:
            raise HTTPException(status_code=404, detail="Application not found")
        notes = app_obj.metadata.get('notes', [])
        note = {"id": str(uuid.uuid4()), "note": body.note,
                "added_by": str(current_user.id), "created_at": datetime.now().isoformat()}
        notes.append(note)
        app_obj.metadata['notes'] = notes
        app_obj.save(update_fields=['metadata'])
        return note

    try:
        note = await sync_to_async(_add_note, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "note_id": note['id']}


@router.get("/applications/{application_id}/notes/", summary="List application notes")
async def list_application_notes(application_id: str, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobApplication

    def _list():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            app_obj = JobApplication.objects.select_related('job').get(
                id=application_id, job__hospital=hu.hospital
            )
        except JobApplication.DoesNotExist:
            raise HTTPException(status_code=404, detail="Application not found")
        return app_obj.metadata.get('notes', [])

    try:
        notes = await sync_to_async(_list, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"notes": notes, "total": len(notes)}


# ── PATCH Job ─────────────────────────────────────────────────

class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=160)
    description: Optional[str] = None
    responsibilities: Optional[str] = None
    requirements: Optional[str] = None
    salary_min: Optional[Decimal] = Field(None, ge=0)
    salary_max: Optional[Decimal] = Field(None, ge=0)
    salary_visibility: Optional[SalaryVisibility] = None
    is_urgent: Optional[bool] = None
    positions: Optional[int] = Field(None, ge=1)
    closing_date: Optional[datetime] = None


@router.patch("/{job_id}/", response_model=JobCreateOut, summary="Update job posting")
async def update_job(job_id: str, body: JobUpdate, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobPost

    def _update():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            job = JobPost.objects.get(id=job_id, hospital=hu.hospital)
        except JobPost.DoesNotExist:
            raise HTTPException(status_code=404, detail="Job not found")
        for field, value in body.model_dump(exclude_none=True).items():
            if field == 'salary_visibility' and value:
                value = value.value if hasattr(value, 'value') else value
            setattr(job, field, value)
        job.save()
        return job

    try:
        job = await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return JobCreateOut(id=str(job.id), title=job.title, status=job.status, created_at=job.created_at.isoformat())


# ── Job Matches ───────────────────────────────────────────────

@router.get("/{job_id}/matches/", summary="Get matched doctors for a job")
async def get_job_matches(
    job_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobPost
    from apps.doctors.models import DoctorProfile

    def _match():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            job = JobPost.objects.get(id=job_id, hospital=hu.hospital)
        except JobPost.DoesNotExist:
            raise HTTPException(status_code=404, detail="Job not found")
        qs = DoctorProfile.objects.filter(
            verification_status='VERIFIED',
            open_to_opportunities=True,
            experience_years__gte=job.experience_min_years,
        )
        if job.specialty_id:
            qs = qs.filter(primary_specialization_id=job.specialty_id)
        total = qs.count()
        results = list(qs[(page - 1) * page_size: page * page_size])
        return total, results, job

    try:
        total, doctors, job = await sync_to_async(_match, thread_sensitive=True)()
    except HTTPException:
        raise
    return {
        "job_id": job_id, "total": total, "page": page,
        "matched_doctors": [{
            "doctor_id": str(d.id), "full_name": f"Dr. {d.full_name}",
            "headline": d.headline, "experience_years": float(d.experience_years),
            "verification_status": d.verification_status,
            "location": d.professional_location or {},
        } for d in doctors]
    }


# ── Application Invite ────────────────────────────────────────

@router.post("/applications/{application_id}/invite/", status_code=201, summary="Invite doctor to apply")
async def invite_doctor_to_apply(
    application_id: str,
    doctor_id: str,
    job_id: str,
    current_user=Depends(get_current_user),
):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobApplication, JobPost
    from apps.doctors.models import DoctorProfile

    def _invite():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            job = JobPost.objects.get(id=job_id, hospital=hu.hospital, status='PUBLISHED')
        except JobPost.DoesNotExist:
            raise HTTPException(status_code=404, detail="Job not found")
        try:
            doctor = DoctorProfile.objects.get(id=doctor_id)
        except DoctorProfile.DoesNotExist:
            raise HTTPException(status_code=404, detail="Doctor not found")
        if JobApplication.objects.filter(job=job, doctor=doctor).exists():
            raise HTTPException(status_code=409, detail="Doctor already applied")
        app = JobApplication.objects.create(
            job=job, doctor=doctor, status='APPLIED',
            metadata={"invited_by": str(current_user.id)},
        )
        return app

    try:
        app = await sync_to_async(_invite, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "application_id": str(app.id), "status": "INVITED"}


# ── Job Recommendations ───────────────────────────────────────

@router.get("/recommendations/", summary="Get recommended jobs for doctor")
async def job_recommendations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_doctor=Depends(get_current_doctor),
):
    from apps.jobs.models import JobPost

    def _recommend():
        qs = JobPost.objects.filter(status='PUBLISHED').select_related('hospital')
        if current_doctor.primary_specialization_id:
            qs = qs.filter(specialty_id=current_doctor.primary_specialization_id)
        qs = qs.filter(experience_min_years__lte=current_doctor.experience_years)
        total = qs.count()
        results = list(qs.order_by('-published_at')[(page - 1) * page_size: page * page_size])
        return total, results

    total, jobs = await sync_to_async(_recommend, thread_sensitive=True)()
    return {
        "total": total, "page": page,
        "results": [{
            "id": str(j.id), "title": j.title,
            "hospital_name": j.hospital.name, "job_type": j.job_type,
            "location": j.location or {}, "is_urgent": j.is_urgent,
            "salary_min": str(j.salary_min) if j.salary_min else None,
            "salary_visibility": j.salary_visibility,
        } for j in jobs]
    }


# ── Applications Router — /api/v1/applications/ (README spec) ─

applications_router = APIRouter(prefix="/api/v1/applications", tags=["Applications"])


class InviteBody(BaseModel):
    doctor_id: str
    job_id: str


@applications_router.post("/{application_id}/interview/", status_code=201, summary="Schedule interview")
async def _schedule_interview(application_id: str, body: InterviewCreate, current_user=Depends(get_current_user)):
    return await schedule_interview(application_id, body, current_user)


@applications_router.patch("/{application_id}/interview/{interview_id}/", summary="Update interview outcome")
async def _update_interview(application_id: str, interview_id: str, outcome: str, notes: Optional[str] = None, current_user=Depends(get_current_user)):
    return await update_interview_outcome(application_id, interview_id, outcome, notes, current_user)


@applications_router.post("/{application_id}/offer/", status_code=201, summary="Send offer")
async def _send_offer(application_id: str, body: OfferCreate, current_user=Depends(get_current_user)):
    return await send_offer(application_id, body, current_user)


@applications_router.post("/{application_id}/notes/", status_code=201, summary="Add internal note")
async def _add_note(application_id: str, body: NoteCreate, current_user=Depends(get_current_user)):
    return await add_application_note(application_id, body, current_user)


@applications_router.get("/{application_id}/notes/", summary="List application notes")
async def _list_notes(application_id: str, current_user=Depends(get_current_user)):
    return await list_application_notes(application_id, current_user)


@applications_router.post("/{application_id}/invite/", status_code=201, summary="Invite doctor to apply")
async def _invite_doctor(application_id: str, body: InviteBody, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    from apps.jobs.models import JobApplication, JobPost
    from apps.doctors.models import DoctorProfile

    def _invite():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            job = JobPost.objects.get(id=body.job_id, hospital=hu.hospital, status='PUBLISHED')
        except JobPost.DoesNotExist:
            raise HTTPException(status_code=404, detail="Job not found")
        try:
            doctor = DoctorProfile.objects.get(id=body.doctor_id)
        except DoctorProfile.DoesNotExist:
            raise HTTPException(status_code=404, detail="Doctor not found")
        if JobApplication.objects.filter(job=job, doctor=doctor).exists():
            raise HTTPException(status_code=409, detail="Doctor already applied")
        app = JobApplication.objects.create(
            job=job, doctor=doctor, status='APPLIED',
            metadata={"invited_by": str(current_user.id)},
        )
        return app

    try:
        app = await sync_to_async(_invite, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "application_id": str(app.id), "status": "INVITED"}
