from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
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


# ── Helper ────────────────────────────────────────────────────

def _hospital_dict(h) -> HospitalOut:
    return HospitalOut(
        id=str(h.id),
        name=h.name,
        type=h.type,
        about=h.about,
        location=h.location or {},
        bed_count=h.bed_count,
        phone=h.phone,
        email=h.email,
        website=h.website,
        verification_status=h.verification_status,
        logo_file_id=str(h.logo_file_id) if h.logo_file_id else None,
        created_at=h.created_at.isoformat(),
    )


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
    from apps.hospitals.models import HospitalUser

    def _get():
        try:
            return HospitalUser.objects.select_related('hospital').get(user=current_user)
        except HospitalUser.DoesNotExist:
            return None

    hu = await sync_to_async(_get, thread_sensitive=True)()
    if hu is None:
        raise HTTPException(status_code=404, detail="No hospital found")
    return _hospital_dict(hu.hospital)


@router.post("/me/branches/", response_model=BranchCreateOut, status_code=201, summary="Add a branch")
async def add_branch(branch: HospitalBranchCreate, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalBranch, HospitalUser

    def _create():
        try:
            hu = HospitalUser.objects.select_related('hospital').get(user=current_user, role='ADMIN')
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not a hospital admin")
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
    from apps.hospitals.models import HospitalUser

    def _list():
        try:
            hu = HospitalUser.objects.select_related('hospital').get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=404, detail="No hospital found")
        return list(hu.hospital.branches.all())

    try:
        branches = await sync_to_async(_list, thread_sensitive=True)()
    except HTTPException:
        raise
    return [BranchOut(id=str(b.id), name=b.name, location=b.location or {},
                      phone=b.phone, is_primary=b.is_primary) for b in branches]


@router.post("/me/departments/", response_model=DepartmentCreateOut, status_code=201, summary="Add a department")
async def add_department(dept: HospitalDepartmentCreate, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalDepartment, HospitalUser

    def _create():
        try:
            hu = HospitalUser.objects.select_related('hospital').get(user=current_user, role='ADMIN')
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not a hospital admin")
        return HospitalDepartment.objects.create(hospital=hu.hospital, branch_id=dept.branch_id, name=dept.name)

    try:
        d = await sync_to_async(_create, thread_sensitive=True)()
    except HTTPException:
        raise
    return DepartmentCreateOut(id=str(d.id), name=d.name)


@router.get("/me/departments/", response_model=List[DepartmentOut], summary="List departments")
async def list_departments(current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser

    def _list():
        try:
            hu = HospitalUser.objects.select_related('hospital').get(user=current_user)
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=404, detail="No hospital found")
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
        try:
            hu = HospitalUser.objects.select_related('hospital').get(user=current_user, role='ADMIN')
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not a hospital admin")
        User = get_user_model()
        invited, _ = User.objects.get_or_create(
            phone=invite.phone,
            defaults={'user_type': 'HOSPITAL_HR', 'status': 'ACTIVE'},
        )
        if HospitalUser.objects.filter(user=invited).exists():
            raise HTTPException(status_code=409, detail="User already in a hospital")
        HospitalUser.objects.create(
            user=invited, hospital=hu.hospital, role=invite.role.value,
            designation=invite.designation, branch_id=invite.branch_id, department_id=invite.department_id,
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
        try:
            hu = HospitalUser.objects.select_related('hospital').get(user=current_user, role='ADMIN')
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not a hospital admin")
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
    from apps.hospitals.models import HospitalUser

    def _get_hospital():
        try:
            return HospitalUser.objects.select_related('hospital').get(user=current_user, role='ADMIN')
        except HospitalUser.DoesNotExist:
            raise HTTPException(status_code=403, detail="Not a hospital admin")

    try:
        hu = await sync_to_async(_get_hospital, thread_sensitive=True)()
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
