from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from enum import Enum

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/hospitals", tags=["Hospitals"])


# ── Request Schemas ───────────────────────────────────────────

class Location(BaseModel):
    address: Optional[str] = None
    city: str
    state: str
    pincode: Optional[str] = None
    coordinates: Optional[Dict[str, Any]] = None


class HospitalType(str, Enum):
    HOSPITAL = "HOSPITAL"
    CLINIC = "CLINIC"
    NURSING_HOME = "NURSING_HOME"
    MEDICAL_COLLEGE = "MEDICAL_COLLEGE"


class HospitalAdminRole(str, Enum):
    ADMIN = "ADMIN"
    HR = "HR"
    RECRUITER = "RECRUITER"


class HospitalRegisterRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    type: HospitalType
    about: Optional[str] = None
    location: Location
    bed_count: Optional[int] = Field(None, ge=1)
    hospital_phone: Optional[str] = None
    hospital_email: Optional[EmailStr] = None
    website: Optional[str] = None


class HospitalBranchCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    location: Location
    phone: Optional[str] = None
    is_primary: bool = False


class HospitalDepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    branch_id: Optional[str] = None


class HospitalUserInvite(BaseModel):
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    role: HospitalAdminRole
    designation: Optional[str] = None
    branch_id: Optional[str] = None
    department_id: Optional[str] = None


# ── Response Schemas ──────────────────────────────────────────

class HospitalOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000", "name": "Apollo Hospital",
        "type": "HOSPITAL", "about": "Multi-specialty hospital",
        "location": {"city": "Mumbai", "state": "Maharashtra"},
        "bed_count": 500, "phone": "9876543210", "email": "info@apollo.com",
        "website": "https://apollo.com", "verification_status": "VERIFIED",
        "logo_file_id": None, "created_at": "2025-01-01T00:00:00Z"
    }})
    id: str
    name: str
    type: str
    about: Optional[str]
    location: Dict[str, Any]
    bed_count: Optional[int]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    verification_status: str
    logo_file_id: Optional[str]
    created_at: str


class BranchOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000", "name": "Andheri Branch",
        "location": {"city": "Mumbai", "state": "Maharashtra"}, "phone": "9876543210", "is_primary": False
    }})
    id: str
    name: str
    location: Dict[str, Any]
    phone: Optional[str]
    is_primary: bool


class BranchCreateOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000", "name": "Andheri Branch", "is_primary": False
    }})
    id: str
    name: str
    is_primary: bool


class DepartmentOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000", "name": "Cardiology",
        "branch_id": None, "active": True
    }})
    id: str
    name: str
    branch_id: Optional[str]
    active: bool


class DepartmentCreateOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "id": "550e8400-e29b-41d4-a716-446655440000", "name": "Cardiology"
    }})
    id: str
    name: str


class InviteOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "success": True, "message": "9876543210 added as HR"
    }})
    success: bool
    message: str


class StaffOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000", "phone": "9876543210",
        "role": "HR", "designation": "HR Manager", "status": "ACTIVE"
    }})
    user_id: str
    phone: str
    role: str
    designation: Optional[str]
    status: str


class LogoUploadOut(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {
        "success": True, "file_id": "550e8400-e29b-41d4-a716-446655440000"
    }})
    success: bool
    file_id: str


# ── Helpers ───────────────────────────────────────────────────

def _hospital_dict(h) -> HospitalOut:
    return HospitalOut(
        id=str(h.id), name=h.name, type=h.type, about=h.about,
        location=h.location or {}, bed_count=h.bed_count,
        phone=h.phone, email=h.email, website=h.website,
        verification_status=h.verification_status,
        logo_file_id=str(h.logo_file_id) if h.logo_file_id else None,
        created_at=h.created_at.isoformat(),
    )


def _get_active_admin_hu(current_user):
    """Return HospitalUser for an ACTIVE ADMIN. Raises 403 otherwise."""
    from apps.hospitals.models import HospitalUser
    try:
        return HospitalUser.objects.select_related('hospital').get(
            user=current_user, role='ADMIN', status='ACTIVE'
        )
    except HospitalUser.DoesNotExist:
        raise HTTPException(status_code=403, detail="Not an active hospital admin")


def _get_active_hu(current_user):
    """Return any ACTIVE HospitalUser. Raises 404 otherwise."""
    from apps.hospitals.models import HospitalUser
    try:
        return HospitalUser.objects.select_related('hospital').get(
            user=current_user, status='ACTIVE'
        )
    except HospitalUser.DoesNotExist:
        raise HTTPException(status_code=404, detail="No active hospital membership found")


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/register/", response_model=HospitalOut, status_code=201, summary="Register a new hospital")
async def register_hospital(data: HospitalRegisterRequest, current_user=Depends(get_current_user)):
    from apps.hospitals.models import Hospital, HospitalUser

    def _create():
        if current_user.user_type not in ('HOSPITAL_ADMIN', 'ADMIN'):
            raise HTTPException(status_code=403, detail="Only hospital admins can register")
        if HospitalUser.objects.filter(user=current_user).exists():
            raise HTTPException(status_code=409, detail="Already associated with a hospital")
        hospital = Hospital.objects.create(
            name=data.name, type=data.type.value, about=data.about,
            location=data.location.model_dump(), bed_count=data.bed_count,
            phone=data.hospital_phone,
            email=str(data.hospital_email) if data.hospital_email else None,
            website=data.website, verification_status='PENDING',
        )
        HospitalUser.objects.create(user=current_user, hospital=hospital, role='ADMIN')
        return hospital

    try:
        hospital = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return _hospital_dict(hospital)


@router.get("/me/", response_model=HospitalOut, summary="Get my hospital profile")
async def get_my_hospital(current_user=Depends(get_current_user)):
    def _get():
        return _get_active_hu(current_user)

    try:
        hu = await sync_to_async(_get, thread_sensitive=True)()
    except HTTPException:
        raise
    return _hospital_dict(hu.hospital)


@router.post("/me/branches/", response_model=BranchCreateOut, status_code=201, summary="Add a branch")
async def add_branch(branch: HospitalBranchCreate, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalBranch

    def _create():
        hu = _get_active_admin_hu(current_user)
        return HospitalBranch.objects.create(
            hospital=hu.hospital, name=branch.name,
            location=branch.location.model_dump(), phone=branch.phone, is_primary=branch.is_primary,
        )

    try:
        b = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return BranchCreateOut(id=str(b.id), name=b.name, is_primary=b.is_primary)


@router.get("/me/branches/", response_model=List[BranchOut], summary="List branches")
async def list_branches(current_user=Depends(get_current_user)):
    def _list():
        hu = _get_active_hu(current_user)
        return list(hu.hospital.branches.all())

    try:
        branches = await sync_to_async(_list, thread_sensitive=True)()
    except HTTPException:
        raise
    return [BranchOut(id=str(b.id), name=b.name, location=b.location or {},
                      phone=b.phone, is_primary=b.is_primary) for b in branches]


@router.post("/me/departments/", response_model=DepartmentCreateOut, status_code=201, summary="Add a department")
async def add_department(dept: HospitalDepartmentCreate, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalDepartment

    def _create():
        hu = _get_active_admin_hu(current_user)
        return HospitalDepartment.objects.create(
            hospital=hu.hospital, branch_id=dept.branch_id, name=dept.name
        )

    try:
        d = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return DepartmentCreateOut(id=str(d.id), name=d.name)


@router.get("/me/departments/", response_model=List[DepartmentOut], summary="List departments")
async def list_departments(current_user=Depends(get_current_user)):
    def _list():
        hu = _get_active_hu(current_user)
        return list(hu.hospital.departments.all())

    try:
        depts = await sync_to_async(_list, thread_sensitive=True)()
    except HTTPException:
        raise
    return [DepartmentOut(id=str(d.id), name=d.name,
                          branch_id=str(d.branch_id) if d.branch_id else None, active=d.active) for d in depts]


@router.post("/me/invite-user/", response_model=InviteOut, status_code=201, summary="Invite HR / Recruiter")
async def invite_hospital_user(invite: HospitalUserInvite, current_user=Depends(get_current_user)):
    from django.contrib.auth import get_user_model
    from apps.hospitals.models import HospitalUser

    def _invite():
        hu = _get_active_admin_hu(current_user)
        User = get_user_model()
        invited, _ = User.objects.get_or_create(
            phone=invite.phone,
            defaults={'user_type': 'HOSPITAL_HR', 'status': 'ACTIVE'},
        )
        if HospitalUser.objects.filter(user=invited).exists():
            raise HTTPException(status_code=409, detail="User already in a hospital")
        HospitalUser.objects.create(
            user=invited, hospital=hu.hospital, role=invite.role.value,
            designation=invite.designation, branch_id=invite.branch_id,
            department_id=invite.department_id,
        )
        return invite.phone, invite.role.value

    try:
        phone, role = await sync_to_async(_invite, thread_sensitive=True)()
    except HTTPException:
        raise
    return InviteOut(success=True, message=f"{phone} added as {role}")


@router.get("/me/staff/", response_model=List[StaffOut], summary="List hospital staff")
async def list_staff(current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser

    def _list():
        hu = _get_active_admin_hu(current_user)
        return list(HospitalUser.objects.filter(hospital=hu.hospital).select_related('user'))

    try:
        staff = await sync_to_async(_list, thread_sensitive=True)()
    except HTTPException:
        raise
    return [StaffOut(user_id=str(s.user_id), phone=s.user.phone, role=s.role,
                     designation=s.designation, status=s.status) for s in staff]


@router.post("/me/upload-logo/", response_model=LogoUploadOut, summary="Upload hospital logo")
async def upload_logo(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    from apps.core.services.storage import upload_file_to_s3

    def _get_hu():
        return _get_active_admin_hu(current_user)

    try:
        hu = await sync_to_async(_get_hu, thread_sensitive=True)()
    except HTTPException:
        raise

    if file.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
        raise HTTPException(status_code=400, detail="Only JPEG/PNG/WEBP allowed")
    file_id = await upload_file_to_s3(file, folder="hospital-logos")

    await sync_to_async(lambda: (
        setattr(hu.hospital, 'logo_file_id', file_id),
        hu.hospital.save(update_fields=['logo_file_id'])
    ), thread_sensitive=True)()
    return LogoUploadOut(success=True, file_id=str(file_id))


class HospitalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    about: Optional[str] = None
    location: Optional[Location] = None
    bed_count: Optional[int] = Field(None, ge=1)
    hospital_phone: Optional[str] = None
    hospital_email: Optional[EmailStr] = None
    website: Optional[str] = None


@router.patch("/me/", response_model=HospitalOut, summary="Update hospital profile")
async def update_hospital(data: HospitalUpdate, current_user=Depends(get_current_user)):
    def _update():
        hu = _get_active_admin_hu(current_user)
        h = hu.hospital
        if data.name:
            h.name = data.name
        if data.about is not None:
            h.about = data.about
        if data.location:
            h.location = data.location.model_dump()
        if data.bed_count is not None:
            h.bed_count = data.bed_count
        if data.hospital_phone is not None:
            h.phone = data.hospital_phone
        if data.hospital_email is not None:
            h.email = str(data.hospital_email)
        if data.website is not None:
            h.website = data.website
        h.save()
        return h

    try:
        hospital = await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return _hospital_dict(hospital)


@router.post("/me/verification/submit/", summary="Submit hospital verification documents")
async def submit_hospital_verification(current_user=Depends(get_current_user)):
    def _submit():
        hu = _get_active_admin_hu(current_user)
        h = hu.hospital
        if h.verification_status not in ('UNVERIFIED', 'REJECTED'):
            raise HTTPException(status_code=400, detail=f"Cannot submit from status: {h.verification_status}")
        h.verification_status = 'PENDING'
        h.save(update_fields=['verification_status'])
        return h

    try:
        h = await sync_to_async(_submit, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"success": True, "verification_status": "PENDING", "hospital_id": str(h.id)}


@router.get("/me/verification/", summary="Get hospital verification status")
async def get_hospital_verification(current_user=Depends(get_current_user)):
    def _get():
        hu = _get_active_hu(current_user)
        return hu.hospital

    try:
        h = await sync_to_async(_get, thread_sensitive=True)()
    except HTTPException:
        raise
    return {"verification_status": h.verification_status,
            "verified_at": h.verified_at.isoformat() if h.verified_at else None}


# ── Candidate Discovery ──────────────────────────────────────

@router.get("/me/candidates/", summary="Search & filter doctors (candidate discovery)")
async def search_candidates(
    specialty: Optional[str] = Query(None),
    qualification: Optional[str] = Query(None),
    experience_min: Optional[float] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    verified_only: bool = Query(True),
    available_now: bool = Query(False),
    locum_available: bool = Query(False),
    visiting_available: bool = Query(False),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    def _get_hu():
        return _get_active_hu(current_user)

    try:
        await sync_to_async(_get_hu, thread_sensitive=True)()
    except HTTPException:
        raise

    def _search():
        from apps.doctors.models import DoctorProfile
        from apps.availability.models import DoctorAvailability
        from django.db.models import Q
        from django.utils import timezone

        qs = DoctorProfile.objects.all()
        if verified_only:
            qs = qs.filter(verification_status='VERIFIED')
        if specialty:
            qs = qs.filter(primary_specialization_id=specialty)
        if experience_min is not None:
            qs = qs.filter(experience_years__gte=experience_min)
        if city:
            qs = qs.filter(professional_location__city__icontains=city)
        if state:
            qs = qs.filter(professional_location__state__icontains=state)
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search) |
                Q(headline__icontains=search)
            )
        if available_now or locum_available or visiting_available:
            today = timezone.now().date()
            avail_qs = DoctorAvailability.objects.filter(
                is_active=True,
                available_from__lte=today,
                available_until__gte=today,
            )
            if locum_available:
                avail_qs = avail_qs.filter(availability_type='LOCUM')
            elif visiting_available:
                avail_qs = avail_qs.filter(availability_type='VISITING')
            doctor_ids = avail_qs.values_list('doctor_id', flat=True)
            qs = qs.filter(id__in=doctor_ids)
        total = qs.count()
        results = list(qs.order_by('-experience_years')[(page - 1) * page_size: page * page_size])
        return total, results

    total, results = await sync_to_async(_search, thread_sensitive=True)()
    return {
        "total": total, "page": page,
        "results": [{
            "id": str(d.id), "full_name": d.full_name, "headline": d.headline,
            "experience_years": float(d.experience_years),
            "verification_status": d.verification_status,
            "open_to_opportunities": d.open_to_opportunities,
            "location": d.professional_location or {},
            "primary_specialization_id": str(d.primary_specialization_id) if d.primary_specialization_id else None,
        } for d in results]
    }


@router.get("/{hospital_id}/", response_model=HospitalOut, summary="View public hospital profile")
async def get_hospital_public(hospital_id: str, current_user=Depends(get_current_user)):
    from apps.hospitals.models import Hospital

    def _get():
        try:
            return Hospital.objects.get(id=hospital_id, verification_status='VERIFIED')
        except Hospital.DoesNotExist:
            raise HTTPException(status_code=404, detail="Hospital not found")

    try:
        h = await sync_to_async(_get, thread_sensitive=True)()
    except HTTPException:
        raise
    return _hospital_dict(h)


# ── Branch PATCH / DELETE ─────────────────────────────────────

@router.patch("/me/branches/{branch_id}/", response_model=BranchOut, summary="Update branch")
async def update_branch(branch_id: str, branch: HospitalBranchCreate, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalBranch

    def _update():
        hu = _get_active_admin_hu(current_user)
        try:
            b = HospitalBranch.objects.get(id=branch_id, hospital=hu.hospital)
        except HospitalBranch.DoesNotExist:
            raise HTTPException(status_code=404, detail="Branch not found")
        b.name = branch.name
        b.location = branch.location.model_dump()
        if branch.phone is not None:
            b.phone = branch.phone
        b.is_primary = branch.is_primary
        b.save()
        return b

    try:
        b = await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return BranchOut(id=str(b.id), name=b.name, location=b.location or {}, phone=b.phone, is_primary=b.is_primary)


@router.delete("/me/branches/{branch_id}/", status_code=204, summary="Deactivate branch")
async def delete_branch(branch_id: str, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalBranch

    def _delete():
        hu = _get_active_admin_hu(current_user)
        deleted = HospitalBranch.objects.filter(id=branch_id, hospital=hu.hospital).delete()[0]
        if not deleted:
            raise HTTPException(status_code=404, detail="Branch not found")

    try:
        await sync_to_async(_delete, thread_sensitive=True)()
    except HTTPException:
        raise


# ── Hospital Users CRUD ───────────────────────────────────────

class HospitalUserUpdate(BaseModel):
    role: Optional[HospitalAdminRole] = None
    designation: Optional[str] = None
    branch_id: Optional[str] = None
    status: Optional[str] = None


@router.post("/me/users/", response_model=InviteOut, status_code=201, summary="Add hospital user")
async def add_hospital_user(invite: HospitalUserInvite, current_user=Depends(get_current_user)):
    from django.contrib.auth import get_user_model
    from apps.hospitals.models import HospitalUser

    def _add():
        hu = _get_active_admin_hu(current_user)
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            phone=invite.phone, defaults={'user_type': 'HOSPITAL_HR', 'status': 'ACTIVE'}
        )
        if HospitalUser.objects.filter(user=user).exists():
            raise HTTPException(status_code=409, detail="User already in a hospital")
        HospitalUser.objects.create(
            user=user, hospital=hu.hospital, role=invite.role.value,
            designation=invite.designation, branch_id=invite.branch_id,
        )
        return invite.phone, invite.role.value

    try:
        phone, role = await sync_to_async(_add, thread_sensitive=True)()
    except HTTPException:
        raise
    return InviteOut(success=True, message=f"{phone} added as {role}")


@router.get("/me/users/", response_model=List[StaffOut], summary="List hospital users")
async def list_hospital_users(current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser

    def _list():
        hu = _get_active_admin_hu(current_user)
        return list(HospitalUser.objects.filter(hospital=hu.hospital).select_related('user'))

    try:
        users = await sync_to_async(_list, thread_sensitive=True)()
    except HTTPException:
        raise
    return [StaffOut(user_id=str(u.user_id), phone=u.user.phone, role=u.role,
                     designation=u.designation, status=u.status) for u in users]


@router.patch("/me/users/{user_id}/", response_model=InviteOut, summary="Update user role/branch/status")
async def update_hospital_user(user_id: str, body: HospitalUserUpdate, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser

    def _update():
        hu = _get_active_admin_hu(current_user)
        try:
            target = HospitalUser.objects.get(user_id=user_id, hospital=hu.hospital)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found")
        if body.role:
            target.role = body.role.value
        if body.designation is not None:
            target.designation = body.designation
        if body.branch_id is not None:
            target.branch_id = body.branch_id
        if body.status:
            target.status = body.status
        target.save()

    try:
        await sync_to_async(_update, thread_sensitive=True)()
    except HTTPException:
        raise
    return InviteOut(success=True, message="User updated")


@router.delete("/me/users/{user_id}/", status_code=204, summary="Revoke user membership")
async def remove_hospital_user(user_id: str, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser

    def _remove():
        hu = _get_active_admin_hu(current_user)
        deleted = HospitalUser.objects.filter(user_id=user_id, hospital=hu.hospital).delete()[0]
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")

    try:
        await sync_to_async(_remove, thread_sensitive=True)()
    except HTTPException:
        raise
