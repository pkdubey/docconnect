from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/search", tags=["Search"])


class SearchResultItem(BaseModel):
    id: str
    type: str  # doctor / hospital / job / community
    title: str
    subtitle: Optional[str]
    meta: Optional[Dict[str, Any]]


class SearchResponse(BaseModel):
    total: int
    results: List[SearchResultItem]


@router.get("/doctors/", response_model=SearchResponse)
async def search_doctors(
    q: str = Query(..., min_length=1),
    specialty: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    experience_min: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.doctors.models import DoctorProfile
    from django.db.models import Q

    def _search():
        qs = DoctorProfile.objects.filter(
            verification_status='VERIFIED'
        ).filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(headline__icontains=q)
        )
        if specialty:
            qs = qs.filter(primary_specialization_id=specialty)
        if city:
            qs = qs.filter(professional_location__city__icontains=city)
        if experience_min is not None:
            qs = qs.filter(experience_years__gte=experience_min)
        total = qs.count()
        results = list(qs[(page - 1) * page_size: page * page_size])
        return total, results

    total, results = await sync_to_async(_search, thread_sensitive=True)()
    return SearchResponse(
        total=total,
        results=[SearchResultItem(
            id=str(d.id), type="doctor",
            title=f"Dr. {d.full_name}",
            subtitle=d.headline,
            meta={"city": (d.professional_location or {}).get("city"), "experience_years": float(d.experience_years)},
        ) for d in results]
    )


@router.get("/hospitals/", response_model=SearchResponse)
async def search_hospitals(
    q: str = Query(..., min_length=1),
    city: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.hospitals.models import Hospital
    from django.db.models import Q

    def _search():
        qs = Hospital.objects.filter(
            verification_status='VERIFIED'
        ).filter(Q(name__icontains=q))
        if city:
            qs = qs.filter(location__city__icontains=city)
        if type:
            qs = qs.filter(type=type)
        total = qs.count()
        results = list(qs[(page - 1) * page_size: page * page_size])
        return total, results

    total, results = await sync_to_async(_search, thread_sensitive=True)()
    return SearchResponse(
        total=total,
        results=[SearchResultItem(
            id=str(h.id), type="hospital",
            title=h.name, subtitle=h.type,
            meta={"city": (h.location or {}).get("city"), "bed_count": h.bed_count},
        ) for h in results]
    )


@router.get("/jobs/", response_model=SearchResponse)
async def search_jobs(
    q: str = Query(..., min_length=1),
    city: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.jobs.models import JobPost
    from django.db.models import Q

    def _search():
        qs = JobPost.objects.filter(status='PUBLISHED').select_related('hospital').filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )
        if city:
            qs = qs.filter(location__city__icontains=city)
        if job_type:
            qs = qs.filter(job_type=job_type)
        total = qs.count()
        results = list(qs[(page - 1) * page_size: page * page_size])
        return total, results

    total, results = await sync_to_async(_search, thread_sensitive=True)()
    return SearchResponse(
        total=total,
        results=[SearchResultItem(
            id=str(j.id), type="job",
            title=j.title, subtitle=j.hospital.name,
            meta={"job_type": j.job_type, "city": (j.location or {}).get("city"), "is_urgent": j.is_urgent},
        ) for j in results]
    )


@router.get("/universal/", response_model=dict)
async def universal_search(
    q: str = Query(..., min_length=1),
    page_size: int = Query(5, ge=1, le=20),
    current_user=Depends(get_current_user),
):
    from apps.doctors.models import DoctorProfile
    from apps.hospitals.models import Hospital
    from apps.jobs.models import JobPost
    from django.db.models import Q

    def _search():
        doctors = list(DoctorProfile.objects.filter(
            verification_status='VERIFIED'
        ).filter(Q(first_name__icontains=q) | Q(last_name__icontains=q))[:page_size])

        hospitals = list(Hospital.objects.filter(
            verification_status='VERIFIED', name__icontains=q
        )[:page_size])

        jobs = list(JobPost.objects.filter(
            status='PUBLISHED'
        ).filter(Q(title__icontains=q)).select_related('hospital')[:page_size])

        return doctors, hospitals, jobs

    doctors, hospitals, jobs = await sync_to_async(_search, thread_sensitive=True)()
    return {
        "query": q,
        "doctors": [{"id": str(d.id), "name": f"Dr. {d.full_name}", "headline": d.headline} for d in doctors],
        "hospitals": [{"id": str(h.id), "name": h.name, "type": h.type} for h in hospitals],
        "jobs": [{"id": str(j.id), "title": j.title, "hospital": j.hospital.name} for j in jobs],
    }


@router.get("/communities/", response_model=SearchResponse)
async def search_communities(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.core.models import Community

    def _search():
        qs = Community.objects.filter(is_active=True, name__icontains=q)
        total = qs.count()
        results = list(qs[(page - 1) * page_size: page * page_size])
        return total, results

    try:
        total, results = await sync_to_async(_search, thread_sensitive=True)()
    except Exception:
        return SearchResponse(total=0, results=[])

    return SearchResponse(
        total=total,
        results=[SearchResultItem(
            id=str(c.id), type="community",
            title=c.name, subtitle=c.description,
            meta={"member_count": c.member_count},
        ) for c in results]
    )
