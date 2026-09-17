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


@router.delete("/{availability_id}/", status_code=204, summary="Deactivate availability")
async def deactivate_availability(availability_id: str, current_doctor=Depends(get_current_doctor)):
    from apps.availability.models import DoctorAvailability

    updated = await sync_to_async(
        lambda: DoctorAvailability.objects.filter(id=availability_id, doctor=current_doctor).update(is_active=False),
        thread_sensitive=True,
    )()
    if not updated:
        raise HTTPException(status_code=404, detail="Availability not found")


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
