from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user, require_admin, require_super_admin

router = APIRouter(prefix="/api/v1/admin", tags=["Admin CRM"])


# ── Helpers ───────────────────────────────────────────────────

def _write_audit(performed_by, action: str, target_type: str = None, target_id=None, metadata: dict = None):
    """Write an AuditLog entry synchronously (call inside sync_to_async blocks)."""
    from apps.core.models import AuditLog
    AuditLog.objects.create(
        action=action,
        target_type=target_type,
        target_id=target_id,
        performed_by=performed_by,
        metadata=metadata or {},
    )


# ── Schemas ───────────────────────────────────────────────────

class VerificationActionBody(BaseModel):
    reason: Optional[str] = None


class UserActionBody(BaseModel):
    reason: str  # required per spec


class ReportActionBody(BaseModel):
    action_notes: Optional[str] = None
    severity: Optional[str] = None


class ModerationBody(BaseModel):
    reason: str
    action: str = "HIDE"  # HIDE / REMOVE / RESTORE


class CommunityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    specialty_id: Optional[str] = None


class MatchingConfigCreate(BaseModel):
    version: str
    weights: Dict[str, float]
    description: Optional[str] = None


class SettingUpdate(BaseModel):
    name: str
    is_active: Optional[bool] = True


class SuccessOut(BaseModel):
    success: bool
    message: str


# ── Dashboard ─────────────────────────────────────────────────

@router.get("/dashboard/")
async def admin_dashboard(current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _stats():
        from apps.accounts.models import User
        from apps.doctors.models import DoctorProfile
        from apps.hospitals.models import Hospital
        from apps.jobs.models import JobPost, JobApplication
        from apps.shifts.models import ShiftRequest
        from apps.core.models import Report, SupportTicket

        return {
            "total_users": User.objects.count(),
            "total_doctors": DoctorProfile.objects.count(),
            "verified_doctors": DoctorProfile.objects.filter(verification_status='VERIFIED').count(),
            "pending_doctor_verifications": DoctorProfile.objects.filter(verification_status='PENDING').count(),
            "total_hospitals": Hospital.objects.count(),
            "verified_hospitals": Hospital.objects.filter(verification_status='VERIFIED').count(),
            "pending_hospital_verifications": Hospital.objects.filter(verification_status='PENDING').count(),
            "total_jobs": JobPost.objects.count(),
            "published_jobs": JobPost.objects.filter(status='PUBLISHED').count(),
            "total_applications": JobApplication.objects.count(),
            "open_reports": Report.objects.filter(status__in=['SUBMITTED', 'UNDER_REVIEW']).count(),
            "open_support_tickets": SupportTicket.objects.filter(status__in=['OPEN', 'IN_PROGRESS']).count(),
            "shift_requests_total": ShiftRequest.objects.count(),
            "shift_requests_completed": ShiftRequest.objects.filter(status='COMPLETED').count(),
        }

    stats = await sync_to_async(_stats, thread_sensitive=True)()
    return {"success": True, "data": stats}


# ── Doctor Verification Queue ─────────────────────────────────

@router.get("/doctors/verification-queue/")
async def doctor_verification_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    require_admin(current_user)

    def _list():
        from apps.doctors.models import DoctorProfile
        from django.utils import timezone
        qs = DoctorProfile.objects.filter(verification_status='PENDING').select_related('user')
        total = qs.count()
        results = list(qs.order_by('created_at')[(page - 1) * page_size: page * page_size])
        now = timezone.now()
        out = []
        for d in results:
            waiting_hours = round((now - d.created_at).total_seconds() / 3600, 1)
            out.append({
                "id": str(d.id), "full_name": d.full_name,
                "phone": d.user.phone, "created_at": d.created_at.isoformat(),
                "waiting_hours": waiting_hours,
            })
        return total, out

    total, results = await sync_to_async(_list, thread_sensitive=True)()
    return {"total": total, "page": page, "results": results}


@router.get("/doctors/verification-cases/{case_id}/")
async def doctor_verification_case(case_id: str, current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _get():
        from apps.doctors.models import DoctorProfile
        try:
            d = DoctorProfile.objects.select_related('user').prefetch_related(
                'registrations', 'qualifications'
            ).get(id=case_id)
        except DoctorProfile.DoesNotExist:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return d

    try:
        d = await sync_to_async(_get, thread_sensitive=True)()
    except HTTPException:
        raise
    return {
        "id": str(d.id), "full_name": d.full_name, "phone": d.user.phone,
        "verification_status": d.verification_status,
        "verification_rejected_reason": d.verification_rejected_reason,
        "registrations": [{"id": str(r.id), "registration_number": r.registration_number,
                           "council_id": str(r.council_id), "registration_year": r.registration_year}
                          for r in d.registrations.all()],
        "qualifications": [{"degree": q.degree, "institution": q.institution, "year": q.year}
                           for q in d.qualifications.all()],
    }


@router.post("/doctors/verification-cases/{case_id}/approve/", response_model=SuccessOut)
async def approve_doctor_verification(case_id: str, current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _approve():
        from apps.doctors.models import DoctorProfile
        updated = DoctorProfile.objects.filter(id=case_id).update(verification_status='VERIFIED')
        if not updated:
            raise HTTPException(status_code=404, detail="Doctor not found")
        _write_audit(current_user, 'DOCTOR_VERIFICATION_APPROVED', 'DoctorProfile', case_id)

    try:
        await sync_to_async(_approve, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Doctor verification approved")


@router.post("/doctors/verification-cases/{case_id}/reject/", response_model=SuccessOut)
async def reject_doctor_verification(
    case_id: str, body: VerificationActionBody, current_user=Depends(get_current_user)
):
    require_admin(current_user)
    if not body.reason:
        raise HTTPException(status_code=400, detail="Reason is required for rejection")

    def _reject():
        from apps.doctors.models import DoctorProfile
        updated = DoctorProfile.objects.filter(id=case_id).update(
            verification_status='REJECTED',
            verification_rejected_reason=body.reason,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Doctor not found")
        _write_audit(current_user, 'DOCTOR_VERIFICATION_REJECTED', 'DoctorProfile', case_id,
                     {"reason": body.reason})

    try:
        await sync_to_async(_reject, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Doctor verification rejected")


@router.post("/doctors/verification-cases/{case_id}/resubmit/", response_model=SuccessOut)
async def allow_doctor_resubmit(case_id: str, current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _resubmit():
        from apps.doctors.models import DoctorProfile
        updated = DoctorProfile.objects.filter(id=case_id, verification_status='REJECTED').update(
            verification_status='UNVERIFIED', verification_rejected_reason=None
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Doctor not found or not in REJECTED state")
        _write_audit(current_user, 'DOCTOR_RESUBMISSION_ALLOWED', 'DoctorProfile', case_id)

    try:
        await sync_to_async(_resubmit, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Doctor can now resubmit verification")


# ── Hospital Verification Queue ───────────────────────────────

@router.get("/hospitals/verification-queue/")
async def hospital_verification_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    require_admin(current_user)

    def _list():
        from apps.hospitals.models import Hospital
        from django.utils import timezone
        qs = Hospital.objects.filter(verification_status='PENDING')
        total = qs.count()
        results = list(qs.order_by('created_at')[(page - 1) * page_size: page * page_size])
        now = timezone.now()
        out = []
        for h in results:
            waiting_hours = round((now - h.created_at).total_seconds() / 3600, 1)
            out.append({
                "id": str(h.id), "name": h.name, "type": h.type,
                "created_at": h.created_at.isoformat(), "waiting_hours": waiting_hours,
            })
        return total, out

    total, results = await sync_to_async(_list, thread_sensitive=True)()
    return {"total": total, "page": page, "results": results}


@router.post("/hospitals/verification-cases/{case_id}/approve/", response_model=SuccessOut)
async def approve_hospital_verification(case_id: str, current_user=Depends(get_current_user)):
    require_admin(current_user)
    from django.utils import timezone

    def _approve():
        from apps.hospitals.models import Hospital
        updated = Hospital.objects.filter(id=case_id).update(
            verification_status='VERIFIED', verified_at=timezone.now()
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Hospital not found")
        _write_audit(current_user, 'HOSPITAL_VERIFICATION_APPROVED', 'Hospital', case_id)

    try:
        await sync_to_async(_approve, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Hospital verification approved")


@router.post("/hospitals/verification-cases/{case_id}/reject/", response_model=SuccessOut)
async def reject_hospital_verification(
    case_id: str, body: VerificationActionBody, current_user=Depends(get_current_user)
):
    require_admin(current_user)
    if not body.reason:
        raise HTTPException(status_code=400, detail="Reason is required for rejection")

    def _reject():
        from apps.hospitals.models import Hospital
        updated = Hospital.objects.filter(id=case_id).update(verification_status='REJECTED')
        if not updated:
            raise HTTPException(status_code=404, detail="Hospital not found")
        _write_audit(current_user, 'HOSPITAL_VERIFICATION_REJECTED', 'Hospital', case_id,
                     {"reason": body.reason})

    try:
        await sync_to_async(_reject, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Hospital verification rejected")


# ── User Management ───────────────────────────────────────────

@router.get("/users/")
async def list_all_users(
    user_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    require_admin(current_user)

    def _list():
        from django.contrib.auth import get_user_model
        from django.db.models import Q
        User = get_user_model()
        qs = User.objects.all()
        if user_type:
            qs = qs.filter(user_type=user_type)
        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(Q(phone__icontains=search) | Q(email__icontains=search))
        total = qs.count()
        results = list(qs.order_by('-created_at')[(page - 1) * page_size: page * page_size])
        return total, results

    total, results = await sync_to_async(_list, thread_sensitive=True)()
    return {
        "total": total, "page": page,
        "results": [{"id": str(u.id), "phone": u.phone, "user_type": u.user_type,
                     "status": u.status, "created_at": u.created_at.isoformat()} for u in results]
    }


def _update_user_status_with_audit(user_id: str, status: str, performed_by, reason: str = None):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    # Platform Admin must not be able to restrict/suspend/deactivate a Super Admin.
    target = User.objects.filter(id=user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.is_super_admin and not performed_by.is_super_admin:
        raise HTTPException(status_code=403, detail="Platform Admin cannot modify a Super Admin account")
    target.status = status
    target.save(update_fields=['status'])
    _write_audit(performed_by, f'USER_{status}', 'User', user_id, {"reason": reason})


@router.post("/users/{user_id}/restrict/", response_model=SuccessOut)
async def restrict_user(user_id: str, body: UserActionBody, current_user=Depends(get_current_user)):
    require_admin(current_user)
    try:
        await sync_to_async(_update_user_status_with_audit, thread_sensitive=True)(
            user_id, 'INACTIVE', current_user, body.reason
        )
    except HTTPException:
        raise
    return SuccessOut(success=True, message="User restricted")


@router.post("/users/{user_id}/suspend/", response_model=SuccessOut)
async def suspend_user(user_id: str, body: UserActionBody, current_user=Depends(get_current_user)):
    require_admin(current_user)
    try:
        await sync_to_async(_update_user_status_with_audit, thread_sensitive=True)(
            user_id, 'SUSPENDED', current_user, body.reason
        )
    except HTTPException:
        raise
    return SuccessOut(success=True, message="User suspended")


@router.post("/users/{user_id}/restore/", response_model=SuccessOut)
async def restore_user(user_id: str, body: UserActionBody, current_user=Depends(get_current_user)):
    require_admin(current_user)
    try:
        await sync_to_async(_update_user_status_with_audit, thread_sensitive=True)(
            user_id, 'ACTIVE', current_user, body.reason
        )
    except HTTPException:
        raise
    return SuccessOut(success=True, message="User restored")


@router.post("/users/{user_id}/deactivate/", response_model=SuccessOut)
async def deactivate_user(user_id: str, body: UserActionBody, current_user=Depends(get_current_user)):
    require_admin(current_user)
    try:
        await sync_to_async(_update_user_status_with_audit, thread_sensitive=True)(
            user_id, 'DELETED', current_user, body.reason
        )
    except HTTPException:
        raise
    return SuccessOut(success=True, message="User deactivated")


# ── Reports Queue ─────────────────────────────────────────────

@router.get("/reports/")
async def list_reports(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    require_admin(current_user)

    def _list():
        from apps.core.models import Report
        qs = Report.objects.select_related('reporter', 'reviewed_by')
        if status:
            qs = qs.filter(status=status)
        if severity:
            qs = qs.filter(severity=severity)
        if target_type:
            qs = qs.filter(target_type=target_type)
        total = qs.count()
        results = list(qs[(page - 1) * page_size: page * page_size])
        return total, results

    total, results = await sync_to_async(_list, thread_sensitive=True)()
    return {
        "total": total, "page": page,
        "results": [{
            "id": str(r.id), "target_type": r.target_type, "target_id": str(r.target_id),
            "reason": r.reason, "severity": r.severity, "status": r.status,
            "reporter_id": str(r.reporter_id), "created_at": r.created_at.isoformat(),
        } for r in results]
    }


@router.get("/reports/{report_id}/")
async def get_report_detail(report_id: str, current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _get():
        from apps.core.models import Report
        try:
            return Report.objects.select_related('reporter', 'reviewed_by').get(id=report_id)
        except Report.DoesNotExist:
            raise HTTPException(status_code=404, detail="Report not found")

    try:
        r = await sync_to_async(_get, thread_sensitive=True)()
    except HTTPException:
        raise
    return {
        "id": str(r.id), "target_type": r.target_type, "target_id": str(r.target_id),
        "reason": r.reason, "description": r.description, "severity": r.severity,
        "status": r.status, "reporter_id": str(r.reporter_id),
        "resolution_notes": r.resolution_notes,
        "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        "created_at": r.created_at.isoformat(),
    }


@router.post("/reports/{report_id}/action/", response_model=SuccessOut)
async def action_report(report_id: str, body: ReportActionBody, current_user=Depends(get_current_user)):
    require_admin(current_user)
    from django.utils import timezone

    def _action():
        from apps.core.models import Report
        try:
            r = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            raise HTTPException(status_code=404, detail="Report not found")
        r.status = 'ACTIONED'
        r.reviewed_by = current_user
        r.resolution_notes = body.action_notes
        if body.severity:
            r.severity = body.severity
        r.resolved_at = timezone.now()
        r.save()
        _write_audit(current_user, 'REPORT_ACTIONED', 'Report', report_id,
                     {"notes": body.action_notes})

    try:
        await sync_to_async(_action, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message=f"Report {report_id} actioned")


@router.post("/reports/{report_id}/dismiss/", response_model=SuccessOut)
async def dismiss_report(report_id: str, body: ReportActionBody, current_user=Depends(get_current_user)):
    require_admin(current_user)
    from django.utils import timezone

    def _dismiss():
        from apps.core.models import Report
        try:
            r = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            raise HTTPException(status_code=404, detail="Report not found")
        r.status = 'DISMISSED'
        r.reviewed_by = current_user
        r.resolution_notes = body.action_notes
        r.resolved_at = timezone.now()
        r.save(update_fields=['status', 'reviewed_by', 'resolution_notes', 'resolved_at'])
        _write_audit(current_user, 'REPORT_DISMISSED', 'Report', report_id)

    try:
        await sync_to_async(_dismiss, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message=f"Report {report_id} dismissed")


@router.post("/reports/{report_id}/escalate/", response_model=SuccessOut)
async def escalate_report(report_id: str, body: ReportActionBody, current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _escalate():
        from apps.core.models import Report
        try:
            r = Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            raise HTTPException(status_code=404, detail="Report not found")
        r.status = 'ESCALATED'
        r.reviewed_by = current_user
        r.resolution_notes = body.action_notes
        r.save(update_fields=['status', 'reviewed_by', 'resolution_notes'])
        _write_audit(current_user, 'REPORT_ESCALATED', 'Report', report_id)

    try:
        await sync_to_async(_escalate, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message=f"Report {report_id} escalated")


# ── Content Moderation ────────────────────────────────────────

@router.post("/posts/{post_id}/moderate/", response_model=SuccessOut)
async def moderate_post(post_id: str, body: ModerationBody, current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _moderate():
        from apps.doctors.models import Post
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise HTTPException(status_code=404, detail="Post not found")
        if body.action == 'REMOVE':
            post.delete()
        else:
            post.metadata['moderated'] = True
            post.metadata['moderation_reason'] = body.reason
            post.metadata['moderation_action'] = body.action
            post.save(update_fields=['metadata'])
        _write_audit(current_user, f'POST_{body.action}', 'Post', post_id, {"reason": body.reason})

    try:
        await sync_to_async(_moderate, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message=f"Post {body.action.lower()}d")


@router.post("/jobs/{job_id}/moderate/", response_model=SuccessOut)
async def moderate_job(job_id: str, body: ModerationBody, current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _moderate():
        from apps.jobs.models import JobPost
        try:
            job = JobPost.objects.get(id=job_id)
        except JobPost.DoesNotExist:
            raise HTTPException(status_code=404, detail="Job not found")
        if body.action == 'REMOVE':
            job.status = 'CLOSED'
            job.save(update_fields=['status'])
        _write_audit(current_user, f'JOB_{body.action}', 'JobPost', job_id, {"reason": body.reason})

    try:
        await sync_to_async(_moderate, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message=f"Job {body.action.lower()}d")


# ── Community Management ──────────────────────────────────────
# NOTE: Community moderator management (add/remove moderators) is Phase 2.
# The CommunityMember model does not yet have a role/is_moderator field.
# Endpoints: POST /admin/communities/{id}/moderators/ and
#            DELETE /admin/communities/{id}/moderators/{user_id}/
# will be implemented in Phase 2 when the CommunityMember model is extended.

@router.post("/communities/", status_code=201)
async def create_community(body: CommunityCreate, current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _create():
        from apps.core.models import Community
        c = Community.objects.create(
            name=body.name, description=body.description,
            specialty_id=body.specialty_id,
        )
        _write_audit(current_user, 'COMMUNITY_CREATED', 'Community', str(c.id), {"name": body.name})
        return c

    try:
        c = await sync_to_async(_create, thread_sensitive=True)()
        return {"success": True, "id": str(c.id), "name": c.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/communities/{community_id}/")
async def update_community(community_id: str, body: CommunityCreate, current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _update():
        from apps.core.models import Community
        try:
            c = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            raise HTTPException(status_code=404, detail="Community not found")
        c.name = body.name
        if body.description is not None:
            c.description = body.description
        c.save()
        _write_audit(current_user, 'COMMUNITY_UPDATED', 'Community', community_id)
        return c

    try:
        c = await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "id": str(c.id), "name": c.name}


@router.post("/communities/{community_id}/archive/", response_model=SuccessOut)
async def archive_community(community_id: str, current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _archive():
        from apps.core.models import Community
        updated = Community.objects.filter(id=community_id).update(is_active=False)
        if not updated:
            raise HTTPException(status_code=404, detail="Community not found")
        _write_audit(current_user, 'COMMUNITY_ARCHIVED', 'Community', community_id)

    try:
        await sync_to_async(_archive, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Community archived")


# ── Audit Logs ────────────────────────────────────────────────

@router.get("/audit-logs/")
async def audit_logs(
    action: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    require_admin(current_user)

    def _list():
        from apps.core.models import AuditLog
        qs = AuditLog.objects.select_related('performed_by').order_by('-created_at')
        if action:
            qs = qs.filter(action__icontains=action)
        if target_type:
            qs = qs.filter(target_type=target_type)
        total = qs.count()
        results = list(qs[(page - 1) * page_size: page * page_size])
        return total, results

    try:
        total, results = await sync_to_async(_list, thread_sensitive=True)()
        return {
            "total": total, "page": page,
            "results": [{
                "id": str(a.id), "action": a.action, "target_type": a.target_type,
                "target_id": str(a.target_id) if a.target_id else None,
                "performed_by": a.performed_by.phone if a.performed_by else None,
                "metadata": a.metadata,
                "created_at": a.created_at.isoformat(),
            } for a in results]
        }
    except Exception:
        return {"total": 0, "page": page, "results": []}


# ── Analytics ─────────────────────────────────────────────────

@router.get("/analytics/overview/")
async def analytics_overview(current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _analytics():
        from django.db.models import Avg, Count, F, ExpressionWrapper, DurationField
        from django.utils import timezone
        from apps.accounts.models import User
        from apps.doctors.models import DoctorProfile, Connection
        from apps.hospitals.models import Hospital
        from apps.jobs.models import JobPost, JobApplication
        from apps.shifts.models import ShiftRequest
        from apps.core.models import Report, SupportTicket

        # Verification turnaround: avg hours from created_at to verified (approximated via updated_at)
        verified_doctors = DoctorProfile.objects.filter(verification_status='VERIFIED')
        doctor_turnaround = None
        if verified_doctors.exists():
            total_secs = sum(
                (d.updated_at - d.created_at).total_seconds()
                for d in verified_doctors.only('created_at', 'updated_at')
            )
            doctor_turnaround = round(total_secs / verified_doctors.count() / 3600, 1)

        verified_hospitals = Hospital.objects.filter(verification_status='VERIFIED', verified_at__isnull=False)
        hospital_turnaround = None
        if verified_hospitals.exists():
            total_secs = sum(
                (h.verified_at - h.created_at).total_seconds()
                for h in verified_hospitals.only('created_at', 'verified_at')
            )
            hospital_turnaround = round(total_secs / verified_hospitals.count() / 3600, 1)

        # Specialty breakdown for verified doctors
        specialty_breakdown = list(
            DoctorProfile.objects.filter(
                verification_status='VERIFIED',
                primary_specialization_id__isnull=False
            ).values('primary_specialization_id').annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        # Application funnel
        app_funnel = {
            s: JobApplication.objects.filter(status=s).count()
            for s in ['APPLIED', 'SHORTLISTED', 'INTERVIEW', 'OFFERED', 'HIRED', 'REJECTED']
        }

        # Shift acceptance/completion rates
        total_shifts = ShiftRequest.objects.count()
        accepted_shifts = ShiftRequest.objects.filter(
            status__in=['ACCEPTED_BY_DOCTOR', 'CONFIRMED_BY_HOSPITAL', 'COMPLETED']
        ).count()
        completed_shifts = ShiftRequest.objects.filter(status='COMPLETED').count()

        # Report resolution time (avg hours)
        resolved_reports = Report.objects.filter(resolved_at__isnull=False)
        report_resolution_hours = None
        if resolved_reports.exists():
            total_secs = sum(
                (r.resolved_at - r.created_at).total_seconds()
                for r in resolved_reports.only('created_at', 'resolved_at')
            )
            report_resolution_hours = round(total_secs / resolved_reports.count() / 3600, 1)

        return {
            "users": {
                "total": User.objects.count(),
                "doctors": User.objects.filter(user_type='DOCTOR').count(),
                "hospital_admins": User.objects.filter(user_type='HOSPITAL_ADMIN').count(),
                "active": User.objects.filter(status='ACTIVE').count(),
            },
            "doctors": {
                "total": DoctorProfile.objects.count(),
                "verified": verified_doctors.count(),
                "pending": DoctorProfile.objects.filter(verification_status='PENDING').count(),
                "open_to_opportunities": DoctorProfile.objects.filter(open_to_opportunities=True).count(),
                "verification_turnaround_hours": doctor_turnaround,
                "specialty_breakdown": [
                    {"specialty_id": str(s['primary_specialization_id']), "count": s['count']}
                    for s in specialty_breakdown
                ],
            },
            "hospitals": {
                "total": Hospital.objects.count(),
                "verified": verified_hospitals.count(),
                "active": Hospital.objects.filter(verification_status='VERIFIED').count(),
                "verification_turnaround_hours": hospital_turnaround,
            },
            "jobs": {
                "total": JobPost.objects.count(),
                "published": JobPost.objects.filter(status='PUBLISHED').count(),
                "filled": JobPost.objects.filter(status='FILLED').count(),
                "urgent": JobPost.objects.filter(is_urgent=True, status='PUBLISHED').count(),
                "application_funnel": app_funnel,
            },
            "connections": {
                "total": Connection.objects.count(),
                "accepted": Connection.objects.filter(status='ACCEPTED').count(),
            },
            "shifts": {
                "total_requests": total_shifts,
                "accepted": accepted_shifts,
                "completed": completed_shifts,
                "acceptance_rate": round(accepted_shifts / total_shifts * 100, 1) if total_shifts else 0,
                "completion_rate": round(completed_shifts / total_shifts * 100, 1) if total_shifts else 0,
            },
            "reports": {
                "total": Report.objects.count(),
                "open": Report.objects.filter(status__in=['SUBMITTED', 'UNDER_REVIEW']).count(),
                "resolution_time_hours": report_resolution_hours,
            },
            "support": {
                "total_tickets": SupportTicket.objects.count(),
                "open": SupportTicket.objects.filter(status__in=['OPEN', 'IN_PROGRESS']).count(),
            },
        }

    stats = await sync_to_async(_analytics, thread_sensitive=True)()
    return {"success": True, "data": stats}


# ── Admin Settings (Specialties / Qualifications / Councils) ──

@router.post("/settings/specialties/", status_code=201)
async def create_specialty(body: SettingUpdate, current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _create():
        from apps.core.models import Specialization
        s, created = Specialization.objects.get_or_create(
            name=body.name, defaults={"is_active": body.is_active}
        )
        if not created:
            raise HTTPException(status_code=409, detail="Specialty already exists")
        _write_audit(current_user, 'SPECIALTY_CREATED', 'Specialization', str(s.id), {"name": body.name})
        return s

    try:
        s = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "id": str(s.id), "name": s.name}


@router.patch("/settings/specialties/{specialty_id}/")
async def update_specialty(specialty_id: str, body: SettingUpdate, current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _update():
        from apps.core.models import Specialization
        updated = Specialization.objects.filter(id=specialty_id).update(
            name=body.name, is_active=body.is_active
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Specialty not found")
        _write_audit(current_user, 'SPECIALTY_UPDATED', 'Specialization', specialty_id)

    try:
        await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "id": specialty_id}


@router.post("/settings/qualifications/", status_code=201)
async def create_qualification(body: SettingUpdate, current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _create():
        from apps.core.models import Qualification
        q, created = Qualification.objects.get_or_create(
            name=body.name, defaults={"is_active": body.is_active}
        )
        if not created:
            raise HTTPException(status_code=409, detail="Qualification already exists")
        _write_audit(current_user, 'QUALIFICATION_CREATED', 'Qualification', str(q.id))
        return q

    try:
        q = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "id": str(q.id), "name": q.name}


# ── Matching Config ───────────────────────────────────────────

@router.get("/matching-configs/")
async def list_matching_configs(current_user=Depends(get_current_user)):
    require_admin(current_user)

    def _list():
        from apps.core.models import MatchingConfig
        return list(MatchingConfig.objects.all())

    configs = await sync_to_async(_list, thread_sensitive=True)()
    return {
        "results": [{
            "id": str(c.id), "version": c.version, "is_active": c.is_active,
            "weights": c.weights, "description": c.description,
            "created_at": c.created_at.isoformat(),
        } for c in configs]
    }


@router.post("/matching-configs/", status_code=201)
async def create_matching_config(body: MatchingConfigCreate, current_user=Depends(get_current_user)):
    require_super_admin(current_user)

    def _create():
        from apps.core.models import MatchingConfig
        if MatchingConfig.objects.filter(version=body.version).exists():
            raise HTTPException(status_code=409, detail="Version already exists")
        c = MatchingConfig.objects.create(
            version=body.version, weights=body.weights,
            description=body.description, approved_by=current_user,
        )
        _write_audit(current_user, 'MATCHING_CONFIG_CREATED', 'MatchingConfig', str(c.id),
                     {"version": body.version})
        return c

    try:
        c = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "id": str(c.id), "version": c.version}


@router.post("/matching-configs/{config_id}/activate/", response_model=SuccessOut)
async def activate_matching_config(config_id: str, current_user=Depends(get_current_user)):
    require_super_admin(current_user)

    def _activate():
        from apps.core.models import MatchingConfig
        # Deactivate all, then activate the selected one
        MatchingConfig.objects.all().update(is_active=False)
        updated = MatchingConfig.objects.filter(id=config_id).update(is_active=True)
        if not updated:
            raise HTTPException(status_code=404, detail="Config not found")
        _write_audit(current_user, 'MATCHING_CONFIG_ACTIVATED', 'MatchingConfig', config_id)

    try:
        await sync_to_async(_activate, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Matching config activated")


# ── Super Admin — Admin User Management ──────────────────────
# Only Super Admin can create/deactivate/modify admin accounts.
# Platform Admin (is_super_admin=False) is blocked from these endpoints.

class AdminUserCreate(BaseModel):
    phone: str
    is_super_admin: bool = False


@router.post("/super/admin-users/", status_code=201, response_model=SuccessOut,
             summary="Super Admin: create a Platform Admin or Super Admin user")
async def create_admin_user(body: AdminUserCreate, current_user=Depends(get_current_user)):
    require_super_admin(current_user)

    def _create():
        import secrets
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(phone=body.phone).exists():
            raise HTTPException(status_code=409, detail="Phone already registered")
        temp_password = secrets.token_urlsafe(16)
        user = User.objects.create_user(
            phone=body.phone,
            user_type='ADMIN',
            password=temp_password,
            is_staff=True,
            is_super_admin=body.is_super_admin,
        )
        _write_audit(current_user, 'ADMIN_USER_CREATED', 'User', str(user.id),
                     {"phone": body.phone, "is_super_admin": body.is_super_admin})
        return temp_password

    try:
        temp_password = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    # Temporary password returned once — must be changed on first login
    return SuccessOut(
        success=True,
        message=f"Admin user created. Temporary password (change immediately): {temp_password}"
    )


@router.post("/super/admin-users/{user_id}/deactivate/", response_model=SuccessOut,
             summary="Super Admin: deactivate an admin user")
async def deactivate_admin_user(
    user_id: str, body: UserActionBody, current_user=Depends(get_current_user)
):
    require_super_admin(current_user)
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    def _deactivate():
        from django.contrib.auth import get_user_model
        User = get_user_model()
        updated = User.objects.filter(id=user_id, user_type='ADMIN').update(
            status='DELETED', is_active=False
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Admin user not found")
        _write_audit(current_user, 'ADMIN_USER_DEACTIVATED', 'User', user_id, {"reason": body.reason})

    try:
        await sync_to_async(_deactivate, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Admin user deactivated")


@router.patch("/super/admin-users/{user_id}/permissions/", response_model=SuccessOut,
              summary="Super Admin: update admin user is_super_admin flag")
async def update_admin_permissions(
    user_id: str, body: AdminUserCreate, current_user=Depends(get_current_user)
):
    require_super_admin(current_user)
    if str(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="Cannot modify your own permissions")

    def _update():
        from django.contrib.auth import get_user_model
        User = get_user_model()
        updated = User.objects.filter(id=user_id, user_type='ADMIN').update(
            is_super_admin=body.is_super_admin
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Admin user not found")
        _write_audit(current_user, 'ADMIN_PERMISSIONS_UPDATED', 'User', user_id,
                     {"is_super_admin": body.is_super_admin})

    try:
        await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return SuccessOut(success=True, message="Admin permissions updated")
