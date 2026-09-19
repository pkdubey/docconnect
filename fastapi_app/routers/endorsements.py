from typing import List, Optional
from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/endorsements", tags=["Endorsements"])


class EndorsementIn(BaseModel):
    doctor_id: str
    skill: str
    note: Optional[str] = None


class EndorsementOut(BaseModel):
    id: str
    endorser_id: str
    endorsed_id: str
    skill: str
    note: Optional[str]
    created_at: str


class SkillSummaryOut(BaseModel):
    skill: str
    count: int


@router.post("/", response_model=EndorsementOut, status_code=201)
async def endorse_doctor(body: EndorsementIn, current_user=Depends(get_current_user)):
    from apps.core.models import Endorsement
    from apps.doctors.models import DoctorProfile

    if current_user.user_type != 'DOCTOR':
        raise HTTPException(status_code=403, detail="Only verified doctors can endorse peers")

    def _create():
        try:
            endorsed = DoctorProfile.objects.get(id=body.doctor_id, verification_status='VERIFIED')
        except DoctorProfile.DoesNotExist:
            raise HTTPException(status_code=404, detail="Doctor not found")
        if str(endorsed.user_id) == str(current_user.id):
            raise HTTPException(status_code=400, detail="Cannot endorse yourself")
        e, created = Endorsement.objects.get_or_create(
            endorser=current_user, endorsed=endorsed, skill=body.skill.strip(),
            defaults={'note': body.note},
        )
        if not created:
            raise HTTPException(status_code=409, detail="Already endorsed this doctor for this skill")
        return e

    try:
        endorsement = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return _out(endorsement)


@router.get("/received/{doctor_id}/", response_model=List[EndorsementOut])
async def get_endorsements(doctor_id: str, current_user=Depends(get_current_user)):
    from apps.core.models import Endorsement

    def _list():
        return list(Endorsement.objects.filter(endorsed_id=doctor_id).select_related('endorser').order_by('-created_at'))

    items = await sync_to_async(_list, thread_sensitive=True)()
    return [_out(e) for e in items]


@router.get("/received/{doctor_id}/skills/", response_model=List[SkillSummaryOut])
async def endorsement_skill_summary(doctor_id: str, current_user=Depends(get_current_user)):
    from apps.core.models import Endorsement
    from django.db.models import Count

    def _summary():
        return list(
            Endorsement.objects.filter(endorsed_id=doctor_id)
            .values('skill').annotate(count=Count('id')).order_by('-count')
        )

    rows = await sync_to_async(_summary, thread_sensitive=True)()
    return [SkillSummaryOut(skill=r['skill'], count=r['count']) for r in rows]


@router.delete("/{endorsement_id}/", status_code=204)
async def remove_endorsement(endorsement_id: str, current_user=Depends(get_current_user)):
    from apps.core.models import Endorsement

    def _delete():
        try:
            e = Endorsement.objects.get(id=endorsement_id, endorser=current_user)
        except Endorsement.DoesNotExist:
            raise HTTPException(status_code=404, detail="Not found")
        e.delete()

    try:
        await sync_to_async(_delete, thread_sensitive=True)()
    except HTTPException:
        raise


def _out(e) -> EndorsementOut:
    return EndorsementOut(
        id=str(e.id), endorser_id=str(e.endorser_id),
        endorsed_id=str(e.endorsed_id), skill=e.skill,
        note=e.note, created_at=e.created_at.isoformat(),
    )
