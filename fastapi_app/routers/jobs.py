from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from fastapi_app.dependencies import get_current_doctor, get_current_user

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


class Location(BaseModel):
    address: Optional[str] = None
    city: str
    state: str
    pincode: Optional[str] = None
    coordinates: Optional[dict] = None


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


@router.post("/", status_code=201)
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
    return {"id": str(jp.id), "title": jp.title, "status": jp.status, "created_at": jp.created_at.isoformat()}


@router.get("/my-applications/")
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
    return {
        "total": total, "page": page,
        "results": [{"application_id": str(a.id), "job_id": str(a.job_id), "job_title": a.job.title,
                     "hospital_name": a.job.hospital.name, "status": a.status,
                     "applied_at": a.applied_at.isoformat()} for a in results],
    }


@router.get("/")
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
        return total, results

    total, results = await sync_to_async(_list, thread_sensitive=True)()
    return {
        "total": total, "page": page, "page_size": page_size,
        "results": [
            {"id": str(j.id), "title": j.title, "hospital_name": j.hospital.name,
             "job_type": j.job_type, "location": j.location, "is_urgent": j.is_urgent,
             "salary_min": str(j.salary_min) if j.salary_min else None,
             "salary_max": str(j.salary_max) if j.salary_max else None,
             "salary_visibility": j.salary_visibility,
             "published_at": j.published_at.isoformat() if j.published_at else None}
            for j in results
        ],
    }


@router.get("/{job_id}/")
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
    return {
        "id": str(j.id), "title": j.title, "hospital_id": str(j.hospital_id),
        "hospital_name": j.hospital.name, "description": j.description,
        "responsibilities": j.responsibilities, "requirements": j.requirements,
        "location": j.location, "job_type": j.job_type, "shift_type": j.shift_type,
        "experience_min_years": float(j.experience_min_years),
        "experience_max_years": float(j.experience_max_years) if j.experience_max_years else None,
        "salary_min": str(j.salary_min) if j.salary_min else None,
        "salary_max": str(j.salary_max) if j.salary_max else None,
        "salary_visibility": j.salary_visibility, "positions": j.positions,
        "is_urgent": j.is_urgent, "closing_date": j.closing_date.isoformat() if j.closing_date else None,
    }


@router.post("/{job_id}/apply/", status_code=201)
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
    return {"success": True, "application_id": str(app_obj.id), "status": app_obj.status}


@router.post("/{job_id}/withdraw/")
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
        return app_obj

    try:
        await sync_to_async(_withdraw, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "status": "WITHDRAWN"}


@router.get("/{job_id}/applications/")
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
    return {
        "total": total, "page": page,
        "results": [{"application_id": str(a.id), "doctor_id": str(a.doctor_id),
                     "doctor_name": a.doctor.full_name, "status": a.status,
                     "applied_at": a.applied_at.isoformat()} for a in results],
    }


@router.patch("/applications/{application_id}/status/")
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
    return {"success": True, "application_id": application_id, "status": body.status}
