from datetime import date, time
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from fastapi_app.dependencies import get_current_doctor, get_current_user

router = APIRouter(prefix="/api/v1/availability", tags=["Availability"])


# ── Request Schemas ───────────────────────────────────────────

class Location(BaseModel):
    address: Optional[str] = None
    city: str
    state: str
    pincode: Optional[str] = None
    coordinates: Optional[Dict[str, Any]] = None


class AvailabilityType(str, Enum):
    LOCUM = "LOCUM"
    VISITING = "VISITING"
    TEMPORARY = "TEMPORARY"
    PART_TIME = "PART_TIME"


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


# ── Response Schemas ──────────────────────────────────────────

class AvailabilityCreateOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "success": True, "availability_id": "550e8400-e29b-41d4-a716-446655440000", "slots_created": 3
    }})
    success: bool
    availability_id: str
    slots_created: int


class AvailabilityOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000", "availability_type": "LOCUM",
        "available_from": "2025-08-15", "available_until": "2025-08-30",
        "preferred_location": {"city": "Mumbai", "state": "Maharashtra"},
        "preferred_radius_km": 50, "minimum_compensation": "8000",
        "currency": "INR", "notes": None, "is_active": True, "created_at": "2025-01-01T00:00:00Z"
    }})
    id: str
    availability_type: str
    available_from: str
    available_until: str
    preferred_location: Optional[Dict[str, Any]]
    preferred_radius_km: Optional[int]
    minimum_compensation: Optional[str]
    currency: str
    notes: Optional[str]
    is_active: bool
    created_at: str


class SlotOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000", "slot_date": "2025-08-15",
        "start_time": "09:00:00", "end_time": "17:00:00", "is_booked": False
    }})
    id: str
    slot_date: str
    start_time: str
    end_time: str
    is_booked: bool


# ── Helper ────────────────────────────────────────────────────

def _avail_dict(a) -> AvailabilityOut:
    return AvailabilityOut(
        id=str(a.id),
        availability_type=a.availability_type,
        available_from=str(a.available_from),
        available_until=str(a.available_until),
        preferred_location=a.preferred_location or None,
        preferred_radius_km=a.preferred_radius_km,
        minimum_compensation=str(a.minimum_compensation) if a.minimum_compensation else None,
        currency=a.currency,
        notes=a.notes,
        is_active=a.is_active,
        created_at=a.created_at.isoformat(),
    )


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/", response_model=AvailabilityCreateOut, status_code=201, summary="Post doctor availability")
async def create_availability(data: AvailabilityCreate, current_doctor=Depends(get_current_doctor)):
    from apps.availability.models import AvailabilitySlot, DoctorAvailability

    def _create():
        avail = DoctorAvailability.objects.create(
            doctor=current_doctor,
            availability_type=data.availability_type.value,
            available_from=data.available_from,
            available_until=data.available_until,
            preferred_location=data.preferred_location.model_dump() if data.preferred_location else None,
            preferred_radius_km=data.preferred_radius_km,
            minimum_compensation=data.minimum_compensation,
            currency=data.currency,
            notes=data.notes,
        )
        slots = [
            AvailabilitySlot(availability=avail, slot_date=s.slot_date,
                             start_time=s.start_time, end_time=s.end_time)
            for s in data.slots
        ]
        AvailabilitySlot.objects.bulk_create(slots)
        return avail, len(slots)

    avail, slot_count = await sync_to_async(_create, thread_sensitive=True)()
    return AvailabilityCreateOut(success=True, availability_id=str(avail.id), slots_created=slot_count)


@router.get("/me/", response_model=List[AvailabilityOut], summary="List my availabilities")
async def list_my_availabilities(
    is_active: Optional[bool] = Query(None),
    current_doctor=Depends(get_current_doctor),
):
    from apps.availability.models import DoctorAvailability

    def _list():
        qs = DoctorAvailability.objects.filter(doctor=current_doctor)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return list(qs.order_by('-created_at'))

    availabilities = await sync_to_async(_list, thread_sensitive=True)()
    return [_avail_dict(a) for a in availabilities]


class AvailabilityUpdate(BaseModel):
    available_from: Optional[date] = None
    available_until: Optional[date] = None
    preferred_location: Optional[Location] = None
    preferred_radius_km: Optional[int] = Field(None, ge=1, le=500)
    minimum_compensation: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


@router.patch("/{availability_id}/", response_model=AvailabilityOut, summary="Update availability")
async def update_availability(availability_id: str, data: AvailabilityUpdate, current_doctor=Depends(get_current_doctor)):
    from apps.availability.models import DoctorAvailability

    def _update():
        try:
            avail = DoctorAvailability.objects.get(id=availability_id, doctor=current_doctor)
        except DoctorAvailability.DoesNotExist:
            raise HTTPException(status_code=404, detail="Availability not found")
        for field, value in data.model_dump(exclude_none=True).items():
            if field == 'preferred_location' and value:
                value = data.preferred_location.model_dump()
            setattr(avail, field, value)
        avail.save()
        return avail

    try:
        avail = await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return _avail_dict(avail)


@router.delete("/{availability_id}/", status_code=204, summary="Deactivate availability")
async def deactivate_availability(availability_id: str, current_doctor=Depends(get_current_doctor)):
    from apps.availability.models import DoctorAvailability
    from apps.shifts.models import ShiftRequest

    def _deactivate():
        try:
            avail = DoctorAvailability.objects.get(id=availability_id, doctor=current_doctor)
        except DoctorAvailability.DoesNotExist:
            raise HTTPException(status_code=404, detail="Availability not found")
        # Warn if there are pending/accepted shift requests linked to this availability's slots
        active_requests = ShiftRequest.objects.filter(
            doctor=current_doctor,
            status__in=('REQUESTED', 'ACCEPTED_BY_DOCTOR', 'CONFIRMED_BY_HOSPITAL'),
            requirement__requirement_date__gte=avail.available_from,
            requirement__requirement_date__lte=avail.available_until,
        ).exists()
        if active_requests:
            raise HTTPException(
                status_code=409,
                detail="Cannot deactivate availability with pending or confirmed shift requests. Cancel those shifts first."
            )
        avail.is_active = False
        avail.save(update_fields=['is_active'])

    try:
        await sync_to_async(_deactivate, thread_sensitive=True)()
    except HTTPException:
        raise


@router.get("/{availability_id}/slots/", response_model=List[SlotOut], summary="List slots for an availability")
async def list_slots(availability_id: str, current_user=Depends(get_current_user)):
    from apps.availability.models import AvailabilitySlot

    slots = await sync_to_async(
        lambda: list(AvailabilitySlot.objects.filter(
            availability_id=availability_id
        ).order_by('slot_date', 'start_time')),
        thread_sensitive=True,
    )()
    return [SlotOut(id=str(s.id), slot_date=str(s.slot_date),
                    start_time=str(s.start_time), end_time=str(s.end_time),
                    is_booked=s.is_booked) for s in slots]


@router.post("/{availability_id}/slots/", response_model=SlotOut, status_code=201, summary="Add slot to availability")
async def add_slot(availability_id: str, slot: SlotCreate, current_doctor=Depends(get_current_doctor)):
    from apps.availability.models import AvailabilitySlot, DoctorAvailability
    from apps.shifts.models import ShiftRequest

    def _create():
        try:
            avail = DoctorAvailability.objects.get(id=availability_id, doctor=current_doctor)
        except DoctorAvailability.DoesNotExist:
            raise HTTPException(status_code=404, detail="Availability not found")
        # Overlap check: flag if doctor has a confirmed/accepted shift on this date+time
        overlap = ShiftRequest.objects.filter(
            doctor=current_doctor,
            status__in=('ACCEPTED_BY_DOCTOR', 'CONFIRMED_BY_HOSPITAL'),
            requirement__requirement_date=slot.slot_date,
            requirement__start_time__lt=slot.end_time,
            requirement__end_time__gt=slot.start_time,
        ).exists()
        if overlap:
            raise HTTPException(
                status_code=409,
                detail="Slot overlaps with an accepted or confirmed shift on this date."
            )
        return AvailabilitySlot.objects.create(
            availability=avail, slot_date=slot.slot_date,
            start_time=slot.start_time, end_time=slot.end_time,
        )

    try:
        s = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return SlotOut(id=str(s.id), slot_date=str(s.slot_date),
                   start_time=str(s.start_time), end_time=str(s.end_time), is_booked=s.is_booked)


@router.patch("/slots/{slot_id}/", response_model=SlotOut, summary="Update a slot")
async def update_slot(slot_id: str, slot: SlotCreate, current_doctor=Depends(get_current_doctor)):
    from apps.availability.models import AvailabilitySlot

    def _update():
        try:
            s = AvailabilitySlot.objects.select_related('availability').get(
                id=slot_id, availability__doctor=current_doctor
            )
        except AvailabilitySlot.DoesNotExist:
            raise HTTPException(status_code=404, detail="Slot not found")
        s.slot_date = slot.slot_date
        s.start_time = slot.start_time
        s.end_time = slot.end_time
        s.save(update_fields=['slot_date', 'start_time', 'end_time'])
        return s

    try:
        s = await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return SlotOut(id=str(s.id), slot_date=str(s.slot_date),
                   start_time=str(s.start_time), end_time=str(s.end_time), is_booked=s.is_booked)


@router.delete("/slots/{slot_id}/", status_code=204, summary="Delete a slot")
async def delete_slot(slot_id: str, current_doctor=Depends(get_current_doctor)):
    from apps.availability.models import AvailabilitySlot

    deleted = await sync_to_async(
        lambda: AvailabilitySlot.objects.filter(
            id=slot_id, availability__doctor=current_doctor
        ).delete()[0],
        thread_sensitive=True,
    )()
    if not deleted:
        raise HTTPException(status_code=404, detail="Slot not found")


class AvailabilityPreferences(BaseModel):
    preferred_availability_types: Optional[List[str]] = None
    preferred_radius_km: Optional[int] = Field(None, ge=1, le=500)
    minimum_compensation: Optional[Decimal] = Field(None, ge=0)
    currency: str = "INR"
    auto_accept: bool = False


@router.get("/preferences/", summary="Get availability preferences")
async def get_availability_preferences(current_doctor=Depends(get_current_doctor)):
    prefs = current_doctor.metadata.get('availability_preferences', {})
    return {"preferences": prefs}


@router.put("/preferences/", summary="Update availability preferences")
async def update_availability_preferences(
    body: AvailabilityPreferences,
    current_doctor=Depends(get_current_doctor),
):
    def _update():
        current_doctor.metadata['availability_preferences'] = body.model_dump()
        current_doctor.save(update_fields=['metadata'])

    await sync_to_async(_update, thread_sensitive=True)()
    return {"success": True, "preferences": body.model_dump()}
