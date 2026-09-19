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


# ── Geospatial radius search (JSONB-based, no PostGIS required) ──────────────
# Uses Haversine formula in Python — works with existing JSONB coordinates field.
# PostGIS PointField migration is deferred to Phase 3.

import math


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.get("/doctors/nearby/", response_model=SearchResponse, summary="Find doctors within radius (km)")
async def search_doctors_nearby(
    lat: float = Query(..., description="Latitude of search centre"),
    lon: float = Query(..., description="Longitude of search centre"),
    radius_km: float = Query(50.0, ge=1, le=500, description="Search radius in kilometres"),
    specialty: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    """
    Returns verified doctors whose `professional_location.coordinates` falls within
    `radius_km` of the given lat/lon. Uses Haversine distance (JSONB coordinates).
    """
    from apps.doctors.models import DoctorProfile

    def _fetch():
        qs = DoctorProfile.objects.filter(
            verification_status='VERIFIED',
            professional_location__has_key='coordinates',
        )
        if specialty:
            qs = qs.filter(primary_specialization_id=specialty)
        return list(qs)

    all_doctors = await sync_to_async(_fetch, thread_sensitive=True)()

    nearby = []
    for d in all_doctors:
        coords = (d.professional_location or {}).get('coordinates') or {}
        try:
            dlat = float(coords.get('lat') or coords.get('latitude') or 0)
            dlon = float(coords.get('lon') or coords.get('lng') or coords.get('longitude') or 0)
        except (TypeError, ValueError):
            continue
        if dlat == 0 and dlon == 0:
            continue
        dist = _haversine_km(lat, lon, dlat, dlon)
        if dist <= radius_km:
            nearby.append((dist, d))

    nearby.sort(key=lambda x: x[0])
    total = len(nearby)
    page_slice = nearby[(page - 1) * page_size: page * page_size]

    return SearchResponse(
        total=total,
        results=[SearchResultItem(
            id=str(d.id), type="doctor",
            title=f"Dr. {d.full_name}",
            subtitle=d.headline,
            meta={
                "city": (d.professional_location or {}).get("city"),
                "experience_years": float(d.experience_years),
                "distance_km": round(dist, 1),
            },
        ) for dist, d in page_slice]
    )


@router.get("/hospitals/nearby/", response_model=SearchResponse, summary="Find hospitals within radius (km)")
async def search_hospitals_nearby(
    lat: float = Query(...),
    lon: float = Query(...),
    radius_km: float = Query(50.0, ge=1, le=500),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    """Returns verified hospitals within radius_km of lat/lon using Haversine distance."""
    from apps.hospitals.models import Hospital

    def _fetch():
        return list(Hospital.objects.filter(
            verification_status='VERIFIED',
            location__has_key='coordinates',
        ))

    all_hospitals = await sync_to_async(_fetch, thread_sensitive=True)()

    nearby = []
    for h in all_hospitals:
        coords = (h.location or {}).get('coordinates') or {}
        try:
            hlat = float(coords.get('lat') or coords.get('latitude') or 0)
            hlon = float(coords.get('lon') or coords.get('lng') or coords.get('longitude') or 0)
        except (TypeError, ValueError):
            continue
        if hlat == 0 and hlon == 0:
            continue
        dist = _haversine_km(lat, lon, hlat, hlon)
        if dist <= radius_km:
            nearby.append((dist, h))

    nearby.sort(key=lambda x: x[0])
    total = len(nearby)
    page_slice = nearby[(page - 1) * page_size: page * page_size]

    return SearchResponse(
        total=total,
        results=[SearchResultItem(
            id=str(h.id), type="hospital",
            title=h.name, subtitle=h.type,
            meta={
                "city": (h.location or {}).get("city"),
                "bed_count": h.bed_count,
                "distance_km": round(dist, 1),
            },
        ) for dist, h in page_slice]
    )
