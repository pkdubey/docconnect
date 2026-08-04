from datetime import date, time
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from fastapi_app.dependencies import get_current_doctor, get_current_user

router = APIRouter(prefix="/api/v1/availability", tags=["Availability"])


# ── Schemas ───────────────────────────────────────────────────

class Location(BaseModel):
    address: Optional[str] = None
    city: str
    state: str
    pincode: Optional[str] = None
    coordinates: Optional[dict] = None


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


def _avail_dict(a):
    return {
        "id": str(a.id),
        "availability_type": a.availability_type,
        "available_from": str(a.available_from),
        "available_until": str(a.available_until),
        "preferred_location": a.preferred_location,
        "preferred_radius_km": a.preferred_radius_km,
        "minimum_compensation": str(a.minimum_compensation) if a.minimum_compensation else None,
        "currency": a.currency,
        "notes": a.notes,
        "is_active": a.is_active,
        "created_at": a.created_at.isoformat(),
    }


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/", status_code=201)
async def create_availability(data: AvailabilityCreate, current_doctor=Depends(get_current_doctor)):
    from apps.availability.models import DoctorAvailability, AvailabilitySlot
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
        AvailabilitySlot(availability=avail, slot_date=s.slot_date, start_time=s.start_time, end_time=s.end_time)
        for s in data.slots
    ]
    AvailabilitySlot.objects.bulk_create(slots)
    return {"success": True, "availability_id": str(avail.id), "slots_created": len(slots)}


@router.get("/me/")
async def list_my_availabilities(
    is_active: Optional[bool] = Query(None),
    current_doctor=Depends(get_current_doctor),
):
    from apps.availability.models import DoctorAvailability
    qs = DoctorAvailability.objects.filter(doctor=current_doctor)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return [_avail_dict(a) for a in qs.order_by('-created_at')]


@router.delete("/{availability_id}/", status_code=204)
async def deactivate_availability(availability_id: str, current_doctor=Depends(get_current_doctor)):
    from apps.availability.models import DoctorAvailability
    updated = DoctorAvailability.objects.filter(id=availability_id, doctor=current_doctor).update(is_active=False)
    if not updated:
        raise HTTPException(status_code=404, detail="Availability not found")


@router.get("/{availability_id}/slots/")
async def list_slots(availability_id: str, current_user=Depends(get_current_user)):
    from apps.availability.models import AvailabilitySlot
    slots = AvailabilitySlot.objects.filter(availability_id=availability_id).order_by('slot_date', 'start_time')
    return [{"id": str(s.id), "slot_date": str(s.slot_date),
             "start_time": str(s.start_time), "end_time": str(s.end_time), "is_booked": s.is_booked}
            for s in slots]
