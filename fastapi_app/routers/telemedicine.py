from typing import List, Optional
from datetime import datetime
from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/telemedicine", tags=["Telemedicine"])


class SessionIn(BaseModel):
    session_type: str = 'CONSULTATION'   # CONSULTATION / PEER_REVIEW
    scheduled_at: datetime
    duration_minutes: int = 30
    guest_doctor_id: Optional[str] = None  # required for PEER_REVIEW
    notes: Optional[str] = None
    meeting_link: Optional[str] = None


class SessionStatusIn(BaseModel):
    status: str  # IN_PROGRESS / COMPLETED / CANCELLED / NO_SHOW


class SessionOut(BaseModel):
    id: str
    host_id: str
    guest_doctor_id: Optional[str]
    session_type: str
    scheduled_at: str
    duration_minutes: int
    status: str
    meeting_link: Optional[str]
    meeting_id: Optional[str]
    notes: Optional[str]
    started_at: Optional[str]
    ended_at: Optional[str]
    created_at: str


def _out(s) -> SessionOut:
    return SessionOut(
        id=str(s.id), host_id=str(s.host_id),
        guest_doctor_id=str(s.guest_doctor_id) if s.guest_doctor_id else None,
        session_type=s.session_type,
        scheduled_at=s.scheduled_at.isoformat(),
        duration_minutes=s.duration_minutes,
        status=s.status,
        meeting_link=s.meeting_link, meeting_id=s.meeting_id,
        notes=s.notes,
        started_at=s.started_at.isoformat() if s.started_at else None,
        ended_at=s.ended_at.isoformat() if s.ended_at else None,
        created_at=s.created_at.isoformat(),
    )


@router.post("/sessions/", response_model=SessionOut, status_code=201)
async def schedule_session(body: SessionIn, current_user=Depends(get_current_user)):
    from apps.core.models import TelemedicineSession
    from apps.doctors.models import DoctorProfile

    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Doctors only")

    def _create():
        try:
            host = current_user.doctor_profile
        except Exception:
            raise HTTPException(status_code=404, detail="Doctor profile not found")

        guest = None
        if body.session_type == 'PEER_REVIEW':
            if not body.guest_doctor_id:
                raise HTTPException(status_code=400, detail="guest_doctor_id required for PEER_REVIEW")
            try:
                guest = DoctorProfile.objects.get(id=body.guest_doctor_id, verification_status='VERIFIED')
            except DoctorProfile.DoesNotExist:
                raise HTTPException(status_code=404, detail="Guest doctor not found")

        return TelemedicineSession.objects.create(
            host=host, guest_doctor=guest,
            session_type=body.session_type,
            scheduled_at=body.scheduled_at,
            duration_minutes=body.duration_minutes,
            notes=body.notes, meeting_link=body.meeting_link,
        )

    try:
        session = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return _out(session)


@router.get("/sessions/", response_model=List[SessionOut])
async def list_my_sessions(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Doctors only")

    def _list():
        qs = current_user.doctor_profile.tele_sessions_hosted.all()
        if status:
            qs = qs.filter(status=status)
        return list(qs[(page - 1) * page_size: page * page_size])

    sessions = await sync_to_async(_list, thread_sensitive=True)()
    return [_out(s) for s in sessions]


@router.get("/sessions/{session_id}/", response_model=SessionOut)
async def get_session(session_id: str, current_user=Depends(get_current_user)):
    from apps.core.models import TelemedicineSession

    def _get():
        try:
            s = TelemedicineSession.objects.get(id=session_id)
        except TelemedicineSession.DoesNotExist:
            raise HTTPException(status_code=404, detail="Session not found")
        doctor = current_user.doctor_profile
        if s.host_id != doctor.id and s.guest_doctor_id != doctor.id:
            raise HTTPException(status_code=403, detail="Access denied")
        return s

    try:
        session = await sync_to_async(_get, thread_sensitive=True)()
    except HTTPException:
        raise
    return _out(session)


@router.patch("/sessions/{session_id}/status/", response_model=SessionOut)
async def update_session_status(session_id: str, body: SessionStatusIn, current_user=Depends(get_current_user)):
    from apps.core.models import TelemedicineSession
    from django.utils import timezone

    VALID = ('IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW')
    if body.status not in VALID:
        raise HTTPException(status_code=400, detail=f"status must be one of {VALID}")

    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Doctors only")

    def _update():
        try:
            s = TelemedicineSession.objects.get(id=session_id, host=current_user.doctor_profile)
        except TelemedicineSession.DoesNotExist:
            raise HTTPException(status_code=404, detail="Session not found")
        s.status = body.status
        if body.status == 'IN_PROGRESS':
            s.started_at = timezone.now()
        elif body.status in ('COMPLETED', 'CANCELLED', 'NO_SHOW'):
            s.ended_at = timezone.now()
        s.save(update_fields=['status', 'started_at', 'ended_at', 'updated_at'])
        return s

    try:
        session = await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return _out(session)
