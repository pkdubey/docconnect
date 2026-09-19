from typing import Optional
from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/analytics", tags=["Hospital Analytics"])


class AnalyticsDashboardOut(BaseModel):
    hospital_id: str
    total_jobs_active: int
    total_jobs_closed: int
    total_applications: int
    total_shortlisted: int
    total_interviewed: int
    total_hired: int
    total_rejected: int
    total_shifts_open: int
    total_shifts_filled: int
    total_shifts_cancelled: int


class SnapshotOut(BaseModel):
    snapshot_date: str
    total_jobs_active: int
    total_applications: int
    total_hired: int
    total_shifts_filled: int
    total_shifts_open: int
    avg_time_to_hire_days: Optional[float]


@router.get("/hospital/dashboard/", response_model=AnalyticsDashboardOut)
async def hospital_dashboard(current_user=Depends(get_current_user)):
    """Live aggregation dashboard for the authenticated hospital admin/HR."""
    if current_user.user_type not in ('HOSPITAL_ADMIN', 'HOSPITAL_HR'):
        raise HTTPException(status_code=403, detail="Hospital users only")

    def _compute():
        from apps.hospitals.models import HospitalUser
        from apps.jobs.models import JobPost, JobApplication
        from apps.shifts.models import ShiftRequirement, ShiftRequest

        try:
            hu = HospitalUser.objects.select_related('hospital').get(user=current_user, status='ACTIVE')
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="No active hospital membership")

        hospital = hu.hospital
        jobs = JobPost.objects.filter(hospital=hospital)
        apps = JobApplication.objects.filter(job__hospital=hospital)
        reqs = ShiftRequirement.objects.filter(hospital=hospital)
        shift_requests = ShiftRequest.objects.filter(requirement__hospital=hospital)

        return {
            'hospital_id': str(hospital.id),
            'total_jobs_active': jobs.filter(status='PUBLISHED').count(),
            'total_jobs_closed': jobs.filter(status__in=['CLOSED', 'FILLED', 'EXPIRED']).count(),
            'total_applications': apps.count(),
            'total_shortlisted': apps.filter(status='SHORTLISTED').count(),
            'total_interviewed': apps.filter(status='INTERVIEW').count(),
            'total_hired': apps.filter(status='HIRED').count(),
            'total_rejected': apps.filter(status='REJECTED').count(),
            'total_shifts_open': reqs.filter(status='OPEN').count(),
            'total_shifts_filled': reqs.filter(status='FILLED').count(),
            'total_shifts_cancelled': shift_requests.filter(status='CANCELLED').count(),
        }

    try:
        data = await sync_to_async(_compute, thread_sensitive=True)()
    except HTTPException:
        raise
    return AnalyticsDashboardOut(**data)


@router.get("/hospital/snapshots/", response_model=list)
async def hospital_snapshots(
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(get_current_user),
):
    """Returns pre-computed daily snapshots for the last N days."""
    if current_user.user_type not in ('HOSPITAL_ADMIN', 'HOSPITAL_HR'):
        raise HTTPException(status_code=403, detail="Hospital users only")

    def _fetch():
        from apps.hospitals.models import HospitalUser
        from apps.core.models import HospitalAnalyticsSnapshot
        from django.utils import timezone
        import datetime

        try:
            hu = HospitalUser.objects.get(user=current_user, status='ACTIVE')
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="No active hospital membership")

        since = timezone.now().date() - datetime.timedelta(days=days)
        return list(
            HospitalAnalyticsSnapshot.objects.filter(
                hospital=hu.hospital, snapshot_date__gte=since
            ).order_by('snapshot_date')
        )

    try:
        snapshots = await sync_to_async(_fetch, thread_sensitive=True)()
    except HTTPException:
        raise

    return [SnapshotOut(
        snapshot_date=str(s.snapshot_date),
        total_jobs_active=s.total_jobs_active,
        total_applications=s.total_applications,
        total_hired=s.total_hired,
        total_shifts_filled=s.total_shifts_filled,
        total_shifts_open=s.total_shifts_open,
        avg_time_to_hire_days=float(s.avg_time_to_hire_days) if s.avg_time_to_hire_days else None,
    ) for s in snapshots]
