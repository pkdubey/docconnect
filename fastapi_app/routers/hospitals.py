from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr, Field
from enum import Enum

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/hospitals", tags=["Hospitals"])


# ── Schemas ───────────────────────────────────────────────────

class Location(BaseModel):
    address: Optional[str] = None
    city: str
    state: str
    pincode: Optional[str] = None
    coordinates: Optional[dict] = None


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
    phone: str = Field(..., pattern=r'^[6-9]\d{9}$')
    email: EmailStr
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
    email: EmailStr
    role: HospitalAdminRole
    designation: Optional[str] = None
    branch_id: Optional[str] = None
    department_id: Optional[str] = None


def _hospital_dict(h):
    return {
        "id": str(h.id),
        "name": h.name,
        "type": h.type,
        "about": h.about,
        "location": h.location,
        "bed_count": h.bed_count,
        "phone": h.phone,
        "email": h.email,
        "website": h.website,
        "verification_status": h.verification_status,
        "logo_file_id": str(h.logo_file_id) if h.logo_file_id else None,
        "created_at": h.created_at.isoformat(),
    }


def _get_admin_hospital(current_user):
    from apps.hospitals.models import HospitalUser
    try:
        return HospitalUser.objects.select_related('hospital').get(user=current_user, role='ADMIN')
    except HospitalUser.DoesNotExist:
        raise HTTPException(status_code=403, detail="Not a hospital admin")


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/register/", status_code=201)
async def register_hospital(data: HospitalRegisterRequest, current_user=Depends(get_current_user)):
    from apps.hospitals.models import Hospital, HospitalUser
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
    return _hospital_dict(hospital)


@router.get("/me/")
async def get_my_hospital(current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    try:
        hu = HospitalUser.objects.select_related('hospital').get(user=current_user)
        return _hospital_dict(hu.hospital)
    except HospitalUser.DoesNotExist:
        raise HTTPException(status_code=404, detail="No hospital found")


@router.post("/me/branches/", status_code=201)
async def add_branch(branch: HospitalBranchCreate, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalBranch
    hu = _get_admin_hospital(current_user)
    b = HospitalBranch.objects.create(
        hospital=hu.hospital, name=branch.name,
        location=branch.location.model_dump(), phone=branch.phone, is_primary=branch.is_primary,
    )
    return {"id": str(b.id), "name": b.name, "is_primary": b.is_primary}


@router.get("/me/branches/")
async def list_branches(current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    try:
        hu = HospitalUser.objects.select_related('hospital').get(user=current_user)
    except HospitalUser.DoesNotExist:
        raise HTTPException(status_code=404, detail="No hospital found")
    return [{"id": str(b.id), "name": b.name, "location": b.location, "phone": b.phone, "is_primary": b.is_primary}
            for b in hu.hospital.branches.all()]


@router.post("/me/departments/", status_code=201)
async def add_department(dept: HospitalDepartmentCreate, current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalDepartment
    hu = _get_admin_hospital(current_user)
    d = HospitalDepartment.objects.create(hospital=hu.hospital, branch_id=dept.branch_id, name=dept.name)
    return {"id": str(d.id), "name": d.name}


@router.get("/me/departments/")
async def list_departments(current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    try:
        hu = HospitalUser.objects.select_related('hospital').get(user=current_user)
    except HospitalUser.DoesNotExist:
        raise HTTPException(status_code=404, detail="No hospital found")
    return [{"id": str(d.id), "name": d.name, "branch_id": str(d.branch_id) if d.branch_id else None, "active": d.active}
            for d in hu.hospital.departments.all()]


@router.post("/me/invite-user/", status_code=201)
async def invite_hospital_user(invite: HospitalUserInvite, current_user=Depends(get_current_user)):
    from django.contrib.auth import get_user_model
    from apps.hospitals.models import HospitalUser
    hu = _get_admin_hospital(current_user)
    User = get_user_model()
    invited, _ = User.objects.get_or_create(
        phone=invite.phone,
        defaults={'email': str(invite.email), 'user_type': 'HOSPITAL_HR', 'status': 'ACTIVE'},
    )
    if HospitalUser.objects.filter(user=invited).exists():
        raise HTTPException(status_code=409, detail="User already in a hospital")
    HospitalUser.objects.create(
        user=invited, hospital=hu.hospital, role=invite.role.value,
        designation=invite.designation, branch_id=invite.branch_id, department_id=invite.department_id,
    )
    return {"success": True, "message": f"{invite.phone} added as {invite.role.value}"}


@router.post("/me/upload-logo/")
async def upload_logo(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    from apps.core.services.storage import upload_file_to_s3
    hu = _get_admin_hospital(current_user)
    if file.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
        raise HTTPException(status_code=400, detail="Only JPEG/PNG/WEBP allowed")
    file_id = await upload_file_to_s3(file, folder="hospital-logos")
    hu.hospital.logo_file_id = file_id
    hu.hospital.save(update_fields=['logo_file_id'])
    return {"success": True, "file_id": str(file_id)}


@router.get("/me/staff/")
async def list_staff(current_user=Depends(get_current_user)):
    from apps.hospitals.models import HospitalUser
    hu = _get_admin_hospital(current_user)
    staff = HospitalUser.objects.filter(hospital=hu.hospital).select_related('user')
    return [{"user_id": str(s.user_id), "phone": s.user.phone, "role": s.role,
             "designation": s.designation, "status": s.status} for s in staff]
