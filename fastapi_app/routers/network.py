from typing import List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_doctor, get_current_user

router = APIRouter(prefix="/api/v1/network", tags=["Network"])


# ── Schemas ───────────────────────────────────────────────────

class ConnectionRequestBody(BaseModel):
    receiver_id: str


class ConnectionOut(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    status: str
    created_at: str


class SuccessOut(BaseModel):
    success: bool
    message: str


class ReportCreate(BaseModel):
    target_type: str  # PROFILE / POST / COMMENT / JOB / HOSPITAL
    target_id: str
    reason: str  # must be a REASON_CODE from Report model
    description: Optional[str] = None
    severity: Optional[str] = "MEDIUM"


# ── Connections ───────────────────────────────────────────────

@router.post("/connections/request/", response_model=ConnectionOut, status_code=201)
async def send_connection_request(body: ConnectionRequestBody, current_doctor=Depends(get_current_doctor)):
    from apps.doctors.models import Connection, DoctorProfile

    def _create():
        try:
            receiver = DoctorProfile.objects.get(id=body.receiver_id)
        except DoctorProfile.DoesNotExist:
            raise HTTPException(status_code=404, detail="Doctor not found")
        if receiver.id == current_doctor.id:
            raise HTTPException(status_code=400, detail="Cannot connect with yourself")
        if Connection.objects.filter(sender=current_doctor, receiver=receiver).exists():
            raise HTTPException(status_code=409, detail="Connection request already sent")
        if Connection.objects.filter(sender=receiver, receiver=current_doctor).exists():
            raise HTTPException(status_code=409, detail="This doctor already sent you a request")
        return Connection.objects.create(sender=current_doctor, receiver=receiver)

    try:
        conn = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return ConnectionOut(id=str(conn.id), sender_id=str(conn.sender_id),
                         receiver_id=str(conn.receiver_id), status=conn.status,
                         created_at=conn.created_at.isoformat())


@router.post("/connections/{connection_id}/accept/", response_model=SuccessOut)
async def accept_connection(connection_id: str, current_doctor=Depends(get_current_doctor)):
    from apps.doctors.models import Connection

    def _accept():
        try:
            conn = Connection.objects.get(id=connection_id, receiver=current_doctor, status='PENDING')
        except Connection.DoesNotExist:
            raise HTTPException(status_code=404, detail="Connection request not found")
        conn.status = 'ACCEPTED'
        conn.save(update_fields=['status', 'updated_at'])

    try:
        await sync_to_async(_accept, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Connection accepted")


@router.post("/connections/{connection_id}/reject/", response_model=SuccessOut)
async def reject_connection(connection_id: str, current_doctor=Depends(get_current_doctor)):
    from apps.doctors.models import Connection

    def _reject():
        try:
            conn = Connection.objects.get(id=connection_id, receiver=current_doctor, status='PENDING')
        except Connection.DoesNotExist:
            raise HTTPException(status_code=404, detail="Connection request not found")
        conn.status = 'DECLINED'
        conn.save(update_fields=['status', 'updated_at'])

    try:
        await sync_to_async(_reject, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Connection declined")


@router.delete("/connections/{connection_id}/", response_model=SuccessOut)
async def remove_connection(connection_id: str, current_doctor=Depends(get_current_doctor)):
    from apps.doctors.models import Connection
    from django.db.models import Q

    def _withdraw():
        try:
            conn = Connection.objects.get(
                id=connection_id
            )
            if conn.sender_id != current_doctor.id and conn.receiver_id != current_doctor.id:
                raise HTTPException(status_code=404, detail="Connection not found")
        except Connection.DoesNotExist:
            raise HTTPException(status_code=404, detail="Connection not found")
        conn.status = 'WITHDRAWN'
        conn.save(update_fields=['status', 'updated_at'])

    try:
        await sync_to_async(_withdraw, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Connection withdrawn")


@router.get("/connections/", response_model=dict)
async def list_connections(
    type: Optional[str] = Query(None, description="sent / received / accepted"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_doctor=Depends(get_current_doctor),
):
    from apps.doctors.models import Connection
    from django.db.models import Q

    def _list():
        if type == 'sent':
            qs = Connection.objects.filter(sender=current_doctor)
        elif type == 'received':
            qs = Connection.objects.filter(receiver=current_doctor, status='PENDING')
        elif type == 'accepted':
            qs = Connection.objects.filter(
                Q(sender=current_doctor) | Q(receiver=current_doctor), status='ACCEPTED'
            )
        else:
            qs = Connection.objects.filter(Q(sender=current_doctor) | Q(receiver=current_doctor))
        total = qs.count()
        results = list(qs.order_by('-created_at')[(page - 1) * page_size: page * page_size])
        return total, results

    total, results = await sync_to_async(_list, thread_sensitive=True)()
    return {
        "total": total, "page": page,
        "results": [{"id": str(c.id), "sender_id": str(c.sender_id),
                     "receiver_id": str(c.receiver_id), "status": c.status,
                     "created_at": c.created_at.isoformat()} for c in results]
    }


# ── Follow / Unfollow ─────────────────────────────────────────

@router.post("/follow/{user_id}/", response_model=SuccessOut, status_code=201)
async def follow_user(user_id: str, current_user=Depends(get_current_user)):
    from apps.hospitals.models import Hospital, HospitalFollow
    from django.contrib.auth import get_user_model

    def _follow():
        User = get_user_model()
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")
        # Follow hospital if target is hospital admin
        if target_user.user_type in ('HOSPITAL_ADMIN',):
            try:
                from apps.hospitals.models import HospitalUser
                hu = HospitalUser.objects.select_related('hospital').get(user=target_user)
                HospitalFollow.objects.get_or_create(user=current_user, hospital=hu.hospital)
                return f"Now following {hu.hospital.name}"
            except Exception:
                pass
        return "Followed"

    try:
        msg = await sync_to_async(_follow, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message=msg)


@router.delete("/follow/{user_id}/", response_model=SuccessOut)
async def unfollow_user(user_id: str, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalFollow
    from django.contrib.auth import get_user_model

    def _unfollow():
        User = get_user_model()
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")
        if target_user.user_type == 'HOSPITAL_ADMIN':
            try:
                from apps.hospitals.models import HospitalUser
                hu = HospitalUser.objects.select_related('hospital').get(user=target_user)
                HospitalFollow.objects.filter(user=current_user, hospital=hu.hospital).delete()
            except Exception:
                pass

    try:
        await sync_to_async(_unfollow, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Unfollowed")


# ── Block / Unblock ───────────────────────────────────────────

@router.post("/block/{user_id}/", response_model=SuccessOut, status_code=201)
async def block_user(user_id: str, current_user=Depends(get_current_user)):
    from apps.messaging.models import ConversationParticipant
    from django.contrib.auth import get_user_model

    def _block():
        User = get_user_model()
        if not User.objects.filter(id=user_id).exists():
            raise HTTPException(status_code=404, detail="User not found")
        blocked = current_user.metadata.get('blocked_users', [])
        if user_id not in blocked:
            blocked.append(user_id)
            current_user.metadata['blocked_users'] = blocked
            current_user.save(update_fields=['metadata'])

    try:
        await sync_to_async(_block, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="User blocked")


@router.delete("/block/{user_id}/", response_model=SuccessOut)
async def unblock_user(user_id: str, current_user=Depends(get_current_user)):
    def _unblock():
        blocked = current_user.metadata.get('blocked_users', [])
        if user_id in blocked:
            blocked.remove(user_id)
            current_user.metadata['blocked_users'] = blocked
            current_user.save(update_fields=['metadata'])

    await sync_to_async(_unblock, thread_sensitive=True)()
    return SuccessOut(success=True, message="User unblocked")


@router.get("/blocked/", response_model=dict)
async def list_blocked(current_user=Depends(get_current_user)):
    blocked = current_user.metadata.get('blocked_users', [])
    return {"blocked_users": blocked, "total": len(blocked)}


# ── Reports ───────────────────────────────────────────────────

@router.post("/reports/", response_model=SuccessOut, status_code=201)
async def submit_report(body: ReportCreate, current_user=Depends(get_current_user)):
    def _report():
        from apps.core.models import Report
        Report.objects.create(
            reporter=current_user,
            target_type=body.target_type,
            target_id=body.target_id,
            reason=body.reason,
            description=body.description,
            severity=body.severity or 'MEDIUM',
        )

    await sync_to_async(_report, thread_sensitive=True)()
    return SuccessOut(success=True, message="Report submitted successfully")


# ── Top-level /api/v1/reports/ (README spec) ─────────────────

reports_router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@reports_router.post("/", response_model=SuccessOut, status_code=201)
async def submit_report_toplevel(body: ReportCreate, current_user=Depends(get_current_user)):
    """Report a profile/post/comment/job/hospital."""
    return await submit_report(body, current_user)
