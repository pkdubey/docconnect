from typing import List, Optional
from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/second-opinions", tags=["Second Opinions"])


class OpinionRequestIn(BaseModel):
    reviewer_id: str
    clinical_summary: str
    is_anonymous: bool = True
    post_id: Optional[str] = None


class OpinionRespondIn(BaseModel):
    action: str   # ACCEPTED / DECLINED
    response: Optional[str] = None


class OpinionCompleteIn(BaseModel):
    response: str


class OpinionOut(BaseModel):
    id: str
    requester_id: str
    reviewer_id: str
    clinical_summary: str
    is_anonymous: bool
    status: str
    response: Optional[str]
    post_id: Optional[str]
    created_at: str


@router.post("/", response_model=OpinionOut, status_code=201)
async def request_second_opinion(body: OpinionRequestIn, current_user=Depends(get_current_user)):
    from apps.core.models import SecondOpinionRequest
    from apps.doctors.models import DoctorProfile, Post

    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Doctors only")

    def _create():
        try:
            requester = current_user.doctor_profile
        except Exception:
            raise HTTPException(status_code=404, detail="Doctor profile not found")
        try:
            reviewer = DoctorProfile.objects.get(id=body.reviewer_id, verification_status='VERIFIED')
        except DoctorProfile.DoesNotExist:
            raise HTTPException(status_code=404, detail="Reviewer not found")
        if requester.id == reviewer.id:
            raise HTTPException(status_code=400, detail="Cannot request opinion from yourself")
        post = None
        if body.post_id:
            try:
                post = Post.objects.get(id=body.post_id)
            except Post.DoesNotExist:
                pass
        return SecondOpinionRequest.objects.create(
            requester=requester, reviewer=reviewer,
            clinical_summary=body.clinical_summary,
            is_anonymous=body.is_anonymous, post=post,
        )

    try:
        req = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return _out(req)


@router.get("/sent/", response_model=List[OpinionOut])
async def my_sent_requests(current_user=Depends(get_current_user)):
    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Doctors only")

    def _list():
        return list(current_user.doctor_profile.opinion_requests_sent.all())

    items = await sync_to_async(_list, thread_sensitive=True)()
    return [_out(r) for r in items]


@router.get("/received/", response_model=List[OpinionOut])
async def my_received_requests(current_user=Depends(get_current_user)):
    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Doctors only")

    def _list():
        return list(current_user.doctor_profile.opinion_requests_received.filter(status='PENDING'))

    items = await sync_to_async(_list, thread_sensitive=True)()
    return [_out(r) for r in items]


@router.patch("/{request_id}/respond/", response_model=OpinionOut)
async def respond_to_request(request_id: str, body: OpinionRespondIn, current_user=Depends(get_current_user)):
    from apps.core.models import SecondOpinionRequest
    from django.utils import timezone

    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Doctors only")
    if body.action not in ('ACCEPTED', 'DECLINED'):
        raise HTTPException(status_code=400, detail="action must be ACCEPTED or DECLINED")

    def _respond():
        try:
            req = SecondOpinionRequest.objects.get(id=request_id, reviewer=current_user.doctor_profile, status='PENDING')
        except SecondOpinionRequest.DoesNotExist:
            raise HTTPException(status_code=404, detail="Request not found")
        req.status = body.action
        if body.response:
            req.response = body.response
        req.responded_at = timezone.now()
        req.save(update_fields=['status', 'response', 'responded_at', 'updated_at'])
        return req

    try:
        req = await sync_to_async(_respond, thread_sensitive=True)()
    except HTTPException:
        raise
    return _out(req)


@router.patch("/{request_id}/complete/", response_model=OpinionOut)
async def complete_request(request_id: str, body: OpinionCompleteIn, current_user=Depends(get_current_user)):
    from apps.core.models import SecondOpinionRequest
    from django.utils import timezone

    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Doctors only")

    def _complete():
        try:
            req = SecondOpinionRequest.objects.get(id=request_id, reviewer=current_user.doctor_profile, status='ACCEPTED')
        except SecondOpinionRequest.DoesNotExist:
            raise HTTPException(status_code=404, detail="Request not found or not accepted")
        req.status = 'COMPLETED'
        req.response = body.response
        req.responded_at = timezone.now()
        req.save(update_fields=['status', 'response', 'responded_at', 'updated_at'])
        return req

    try:
        req = await sync_to_async(_complete, thread_sensitive=True)()
    except HTTPException:
        raise
    return _out(req)


@router.delete("/{request_id}/", status_code=204)
async def cancel_request(request_id: str, current_user=Depends(get_current_user)):
    from apps.core.models import SecondOpinionRequest

    def _cancel():
        try:
            req = SecondOpinionRequest.objects.get(id=request_id, requester=current_user.doctor_profile)
        except SecondOpinionRequest.DoesNotExist:
            raise HTTPException(status_code=404, detail="Not found")
        if req.status in ('COMPLETED',):
            raise HTTPException(status_code=400, detail="Cannot cancel a completed request")
        req.status = 'CANCELLED'
        req.save(update_fields=['status', 'updated_at'])

    try:
        await sync_to_async(_cancel, thread_sensitive=True)()
    except HTTPException:
        raise


def _out(r) -> OpinionOut:
    return OpinionOut(
        id=str(r.id), requester_id=str(r.requester_id),
        reviewer_id=str(r.reviewer_id),
        clinical_summary=r.clinical_summary,
        is_anonymous=r.is_anonymous, status=r.status,
        response=r.response,
        post_id=str(r.post_id) if r.post_id else None,
        created_at=r.created_at.isoformat(),
    )
