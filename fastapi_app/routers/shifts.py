from datetime import date, time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from fastapi_app.dependencies import get_current_doctor, get_current_user

router = APIRouter(prefix="/api/v1/shifts", tags=["Shifts"])


# ── Request Schemas ───────────────────────────────────────────

class Location(BaseModel):
    address: Optional[str] = None
    city: str
    state: str
    pincode: Optional[str] = None
    coordinates: Optional[Dict[str, Any]] = None


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


class ShiftRespondRequest(BaseModel):
    accept: bool


# ── Response Schemas ──────────────────────────────────────────

class ShiftRequirementOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "hospital_id": "550e8400-e29b-41d4-a716-446655440001",
        "specialty_id": "550e8400-e29b-41d4-a716-446655440002",
        "requirement_date": "2025-08-18", "start_time": "08:00:00", "end_time": "20:00:00",
        "location": {"city": "Mumbai", "state": "Maharashtra"},
        "compensation": "12000", "currency": "INR", "doctors_required": 2,
        "urgency": "URGENT", "status": "OPEN", "notes": None, "created_at": "2025-01-01T00:00:00Z"
    }})
    id: str
    hospital_id: str
    specialty_id: str
    requirement_date: str
    start_time: str
    end_time: str
    location: Dict[str, Any]
    compensation: str
    currency: str
    doctors_required: int
    urgency: str
    status: str
    notes: Optional[str]
    created_at: str


class ShiftRequirementsListResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"total": 1, "page": 1, "results": []}})
    total: int
    page: int
    results: List[ShiftRequirementOut]


class ShiftRequestOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "requirement_id": "550e8400-e29b-41d4-a716-446655440001",
        "hospital_name": "Apollo Hospital", "requirement_date": "2025-08-18",
        "start_time": "08:00:00", "end_time": "20:00:00", "compensation": "12000",
        "urgency": "URGENT", "status": "REQUESTED", "requested_at": "2025-01-01T00:00:00Z"
    }})
    id: str
    requirement_id: str
    hospital_name: str
    requirement_date: str
    start_time: str
    end_time: str
    compensation: str
    urgency: str
    status: str
    requested_at: str


class ShiftActionOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"success": True, "status": "ACCEPTED_BY_DOCTOR"}})
    success: bool
    status: str


class MatchedDoctorOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "doctor_id": "550e8400-e29b-41d4-a716-446655440000", "full_name": "Arjun Sharma",
        "headline": "Cardiologist · 12 yrs", "experience_years": 12.0,
        "verification_status": "VERIFIED",
        "availability_id": "550e8400-e29b-41d4-a716-446655440001", "minimum_compensation": "8000"
    }})
    doctor_id: str
    full_name: str
    headline: Optional[str]
    experience_years: float
    verification_status: str
    availability_id: str
    minimum_compensation: Optional[str]


class MatchedDoctorsResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"total": 1, "matched_doctors": []}})
    total: int
    matched_doctors: List[MatchedDoctorOut]


# ── Helper ────────────────────────────────────────────────────

def _req_dict(r) -> ShiftRequirementOut:
    return ShiftRequirementOut(
        id=str(r.id),
        hospital_id=str(r.hospital_id),
        specialty_id=str(r.specialty_id),
        requirement_date=str(r.requirement_date),
        start_time=str(r.start_time),
        end_time=str(r.end_time),
        location=r.location or {},
        compensation=str(r.compensation),
        currency=r.currency,
        doctors_required=r.doctors_required,
        urgency=r.urgency,
        status=r.status,
        notes=r.notes,
        created_at=r.created_at.isoformat(),
    )


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/requirements/", response_model=ShiftRequirementOut, status_code=201, summary="Post a shift requirement")
async def create_shift_requirement(req: ShiftRequirementCreate, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    from apps.shifts.models import ShiftRequirement

    def _create():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        return ShiftRequirement.objects.create(
            hospital=hu.hospital, branch_id=req.branch_id,
            specialty_id=req.specialty_id, qualification_ids=req.qualification_ids,
            requirement_date=req.requirement_date, start_time=req.start_time,
            end_time=req.end_time, location=req.location.model_dump(),
            compensation=req.compensation, currency=req.currency,
            doctors_required=req.doctors_required, urgency=req.urgency,
            notes=req.notes, created_by=current_user,
        )

    try:
        sr = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return _req_dict(sr)


@router.get("/requirements/mine/", response_model=List[ShiftRequirementOut], summary="My hospital's shift requirements")
async def my_hospital_requirements(current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    from apps.shifts.models import ShiftRequirement

    def _list():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        return list(ShiftRequirement.objects.filter(hospital=hu.hospital).order_by('-created_at'))

    try:
        reqs = await sync_to_async(_list, thread_sensitive=True)()
    except HTTPException:
        raise
    return [_req_dict(r) for r in reqs]


@router.get("/requirements/", response_model=ShiftRequirementsListResponse, summary="List open shift requirements")
async def list_shift_requirements(
    urgency: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.shifts.models import ShiftRequirement

    def _list():
        qs = ShiftRequirement.objects.filter(status='OPEN').select_related('hospital')
        if urgency:
            qs = qs.filter(urgency=urgency)
        if city:
            qs = qs.filter(location__city__icontains=city)
        if specialty:
            qs = qs.filter(specialty_id=specialty)
        total = qs.count()
        results = list(qs.order_by('-created_at')[(page - 1) * page_size: page * page_size])
        return total, results

    total, results = await sync_to_async(_list, thread_sensitive=True)()
    return ShiftRequirementsListResponse(total=total, page=page, results=[_req_dict(r) for r in results])


@router.get("/requests/mine/", response_model=List[ShiftRequestOut], summary="Doctor's shift requests")
async def my_shift_requests(current_doctor=Depends(get_current_doctor)):
    from apps.shifts.models import ShiftRequest

    reqs = await sync_to_async(
        lambda: list(ShiftRequest.objects.filter(doctor=current_doctor)
                     .select_related('requirement', 'requirement__hospital')
                     .order_by('-requested_at')),
        thread_sensitive=True,
    )()
    return [ShiftRequestOut(
        id=str(r.id), requirement_id=str(r.requirement_id),
        hospital_name=r.requirement.hospital.name,
        requirement_date=str(r.requirement.requirement_date),
        start_time=str(r.requirement.start_time),
        end_time=str(r.requirement.end_time),
        compensation=str(r.requirement.compensation),
        urgency=r.requirement.urgency, status=r.status,
        requested_at=r.requested_at.isoformat(),
    ) for r in reqs]


@router.post("/requirements/{requirement_id}/request/", response_model=ShiftActionOut, status_code=201, summary="Doctor requests a shift")
async def request_shift(requirement_id: str, current_doctor=Depends(get_current_doctor)):
    from apps.shifts.models import ShiftRequirement, ShiftRequest

    def _create():
        try:
            req = ShiftRequirement.objects.get(id=requirement_id, status='OPEN')
        except ShiftRequirement.DoesNotExist:
            raise HTTPException(status_code=404, detail="Shift requirement not found or not open")
        if ShiftRequest.objects.filter(requirement=req, doctor=current_doctor).exists():
            raise HTTPException(status_code=409, detail="Already requested this shift")
        return ShiftRequest.objects.create(requirement=req, doctor=current_doctor)

    try:
        sr = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return ShiftActionOut(success=True, status=sr.status)


@router.patch("/requests/{request_id}/respond/", response_model=ShiftActionOut, summary="Doctor accepts or declines shift")
async def respond_to_shift(request_id: str, body: ShiftRespondRequest, current_doctor=Depends(get_current_doctor)):
    from apps.shifts.models import ShiftRequest
    from django.utils import timezone

    def _respond():
        try:
            sr = ShiftRequest.objects.get(id=request_id, doctor=current_doctor, status='REQUESTED')
        except ShiftRequest.DoesNotExist:
            raise HTTPException(status_code=404, detail="Shift request not found")
        if body.accept:
            sr.status = 'ACCEPTED_BY_DOCTOR'
            sr.accepted_at = timezone.now()
        else:
            sr.status = 'DECLINED_BY_DOCTOR'
            sr.declined_at = timezone.now()
        sr.save()
        return sr.status

    try:
        new_status = await sync_to_async(_respond, thread_sensitive=True)()
    except HTTPException:
        raise
    return ShiftActionOut(success=True, status=new_status)


@router.patch("/requests/{request_id}/confirm/", response_model=ShiftActionOut, summary="Hospital confirms shift")
async def confirm_shift(request_id: str, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    from apps.shifts.models import ShiftRequest
    from django.utils import timezone

    def _confirm():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            sr = ShiftRequest.objects.select_related('requirement').get(
                id=request_id, requirement__hospital=hu.hospital, status='ACCEPTED_BY_DOCTOR'
            )
        except ShiftRequest.DoesNotExist:
            raise HTTPException(status_code=404, detail="Shift request not found")
        sr.status = 'CONFIRMED_BY_HOSPITAL'
        sr.confirmed_at = timezone.now()
        sr.save()
        return sr.status

    try:
        new_status = await sync_to_async(_confirm, thread_sensitive=True)()
    except HTTPException:
        raise
    return ShiftActionOut(success=True, status=new_status)


@router.patch("/requests/{request_id}/complete/", response_model=ShiftActionOut, summary="Mark shift as completed")
async def complete_shift(request_id: str, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    from apps.shifts.models import ShiftRequest
    from django.utils import timezone

    def _complete():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            sr = ShiftRequest.objects.select_related('requirement').get(
                id=request_id, requirement__hospital=hu.hospital, status='CONFIRMED_BY_HOSPITAL'
            )
        except ShiftRequest.DoesNotExist:
            raise HTTPException(status_code=404, detail="Shift request not found or not confirmed")
        sr.status = 'COMPLETED'
        sr.completed_at = timezone.now()
        sr.save()
        req = sr.requirement
        if req.requests.filter(status__in=['CONFIRMED_BY_HOSPITAL', 'COMPLETED']).count() >= req.doctors_required:
            req.status = 'FILLED'
            req.save(update_fields=['status'])
        return sr.status

    try:
        new_status = await sync_to_async(_complete, thread_sensitive=True)()
    except HTTPException:
        raise
    return ShiftActionOut(success=True, status=new_status)


@router.patch("/requests/{request_id}/cancel/", response_model=ShiftActionOut, summary="Cancel a shift request")
async def cancel_shift_request(request_id: str, current_user=Depends(get_current_user)):
    from apps.shifts.models import ShiftRequest
    from django.utils import timezone

    def _cancel():
        try:
            if current_user.user_type == 'DOCTOR':
                sr = ShiftRequest.objects.get(id=request_id, doctor__user=current_user)
            else:
                from apps.hospitals.models import HospitalUser
                try:
                    hu = HospitalUser.objects.get(user=current_user)
                except HospitalUser.DoesNotExist:
                    raise HTTPException(status_code=403, detail="Not associated with a hospital")
                sr = ShiftRequest.objects.select_related('requirement').get(
                    id=request_id, requirement__hospital=hu.hospital
                )
        except ShiftRequest.DoesNotExist:
            raise HTTPException(status_code=404, detail="Shift request not found")
        if sr.status in ('COMPLETED', 'CANCELLED'):
            raise HTTPException(status_code=400, detail=f"Cannot cancel from status: {sr.status}")
        sr.status = 'CANCELLED'
        sr.cancelled_at = timezone.now()
        sr.save()

    try:
        await sync_to_async(_cancel, thread_sensitive=True)()
    except HTTPException:
        raise
    return ShiftActionOut(success=True, status="CANCELLED")


@router.get("/requirements/{requirement_id}/matched-doctors/", response_model=MatchedDoctorsResponse, summary="Get matched doctors for a shift requirement")
async def matched_doctors(requirement_id: str, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    from apps.shifts.models import ShiftRequirement
    from apps.availability.models import DoctorAvailability

    def _match():
        try:
            hu = HospitalUser.objects.get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not associated with a hospital")
        try:
            req = ShiftRequirement.objects.get(id=requirement_id, hospital=hu.hospital)
        except ShiftRequirement.DoesNotExist:
            raise HTTPException(status_code=404, detail="Requirement not found")

        matched = DoctorAvailability.objects.filter(
            is_active=True,
            available_from__lte=req.requirement_date,
            available_until__gte=req.requirement_date,
        ).select_related('doctor')
        if req.compensation:
            matched = (
                matched.filter(minimum_compensation__lte=req.compensation) |
                DoctorAvailability.objects.filter(
                    is_active=True,
                    available_from__lte=req.requirement_date,
                    available_until__gte=req.requirement_date,
                    minimum_compensation__isnull=True,
                )
            )
        result = []
        seen = set()
        for avail in matched:
            if avail.doctor_id in seen:
                continue
            if avail.slots.filter(
                slot_date=req.requirement_date,
                start_time__lte=req.start_time,
                end_time__gte=req.end_time,
                is_booked=False,
            ).exists():
                seen.add(avail.doctor_id)
                d = avail.doctor
                result.append(MatchedDoctorOut(
                    doctor_id=str(d.id), full_name=d.full_name,
                    headline=d.headline, experience_years=float(d.experience_years),
                    verification_status=d.verification_status,
                    availability_id=str(avail.id),
                    minimum_compensation=str(avail.minimum_compensation) if avail.minimum_compensation else None,
                ))
        return result

    try:
        result = await sync_to_async(_match, thread_sensitive=True)()
    except HTTPException:
        raise
    return MatchedDoctorsResponse(total=len(result), matched_doctors=result)
