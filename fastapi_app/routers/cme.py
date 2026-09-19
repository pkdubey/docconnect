from typing import List, Optional
from datetime import date
from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/cme", tags=["CME Credits"])


class CMEEventOut(BaseModel):
    id: str
    title: str
    provider: str
    credit_hours: float
    event_date: str
    specialty_id: Optional[str]


class CMECreditIn(BaseModel):
    title: str
    provider: Optional[str] = None
    credits: float
    completion_date: date
    event_id: Optional[str] = None
    certificate_file_id: Optional[str] = None


class CMECreditOut(BaseModel):
    id: str
    title: str
    provider: Optional[str]
    credits: float
    completion_date: str
    status: str
    event_id: Optional[str]
    certificate_file_id: Optional[str]
    created_at: str


class CMESummaryOut(BaseModel):
    total_credits: float
    verified_credits: float
    pending_credits: float
    total_entries: int


def _credit_out(c) -> CMECreditOut:
    return CMECreditOut(
        id=str(c.id), title=c.title, provider=c.provider,
        credits=float(c.credits), completion_date=str(c.completion_date),
        status=c.status, event_id=str(c.event_id) if c.event_id else None,
        certificate_file_id=str(c.certificate_file_id) if c.certificate_file_id else None,
        created_at=c.created_at.isoformat(),
    )


@router.get("/events/", response_model=List[CMEEventOut])
async def list_cme_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    from apps.core.models import CMEEvent

    def _list():
        qs = CMEEvent.objects.filter(is_active=True)
        return list(qs[(page - 1) * page_size: page * page_size])

    events = await sync_to_async(_list, thread_sensitive=True)()
    return [CMEEventOut(
        id=str(e.id), title=e.title, provider=e.provider,
        credit_hours=float(e.credit_hours), event_date=str(e.event_date),
        specialty_id=str(e.specialty_id) if e.specialty_id else None,
    ) for e in events]


@router.post("/credits/", response_model=CMECreditOut, status_code=201)
async def log_cme_credit(body: CMECreditIn, current_user=Depends(get_current_user)):
    from apps.core.models import CMECredit, CMEEvent

    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Doctors only")

    def _create():
        try:
            doctor = current_user.doctor_profile
        except Exception:
            raise HTTPException(status_code=404, detail="Doctor profile not found")
        event = None
        if body.event_id:
            try:
                event = CMEEvent.objects.get(id=body.event_id)
            except CMEEvent.DoesNotExist:
                raise HTTPException(status_code=404, detail="CME event not found")
        return CMECredit.objects.create(
            doctor=doctor, event=event, title=body.title,
            provider=body.provider, credits=body.credits,
            completion_date=body.completion_date,
            certificate_file_id=body.certificate_file_id,
        )

    try:
        credit = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return _credit_out(credit)


@router.get("/credits/", response_model=List[CMECreditOut])
async def list_my_cme_credits(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Doctors only")

    def _list():
        qs = current_user.doctor_profile.cme_credits.all()
        if status:
            qs = qs.filter(status=status)
        return list(qs[(page - 1) * page_size: page * page_size])

    credits = await sync_to_async(_list, thread_sensitive=True)()
    return [_credit_out(c) for c in credits]


@router.get("/credits/summary/", response_model=CMESummaryOut)
async def cme_summary(current_user=Depends(get_current_user)):
    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Doctors only")

    def _summary():
        from django.db.models import Sum
        qs = current_user.doctor_profile.cme_credits.all()
        total = float(qs.aggregate(s=Sum('credits'))['s'] or 0)
        verified = float(qs.filter(status='VERIFIED').aggregate(s=Sum('credits'))['s'] or 0)
        pending = float(qs.filter(status='PENDING').aggregate(s=Sum('credits'))['s'] or 0)
        return total, verified, pending, qs.count()

    total, verified, pending, count = await sync_to_async(_summary, thread_sensitive=True)()
    return CMESummaryOut(total_credits=total, verified_credits=verified, pending_credits=pending, total_entries=count)


@router.delete("/credits/{credit_id}/", status_code=204)
async def delete_cme_credit(credit_id: str, current_user=Depends(get_current_user)):
    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Doctors only")

    def _delete():
        from apps.core.models import CMECredit
        try:
            c = CMECredit.objects.get(id=credit_id, doctor=current_user.doctor_profile)
        except CMECredit.DoesNotExist:
            raise HTTPException(status_code=404, detail="Not found")
        if c.status == 'VERIFIED':
            raise HTTPException(status_code=400, detail="Cannot delete a verified credit")
        c.delete()

    try:
        await sync_to_async(_delete, thread_sensitive=True)()
    except HTTPException:
        raise
