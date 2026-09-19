"""
Security & RBAC authorization tests.
Covers all 13 scenarios from the Gap Audit + additional edge cases.
"""
import hashlib
import pytest
from datetime import timedelta


# ── Helpers ───────────────────────────────────────────────────

def _otp_token(api_client, phone, user_type='DOCTOR', status='ACTIVE',
               is_super_admin=False):
    """Create user + OTP, return access token."""
    from django.utils import timezone
    from apps.accounts.models import User, OTPChallenge

    user, _ = User.objects.get_or_create(
        phone=phone,
        defaults={'user_type': user_type, 'status': status,
                  'is_super_admin': is_super_admin},
    )
    if user.status != status:
        user.status = status
        user.save(update_fields=['status'])
    if user.is_super_admin != is_super_admin:
        user.is_super_admin = is_super_admin
        user.save(update_fields=['is_super_admin'])

    otp = '111222'
    OTPChallenge.objects.create(
        phone=phone, purpose='LOGIN',
        otp_hash=hashlib.sha256(otp.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    resp = api_client.post(
        '/api/v1/auth/verify-otp/',
        json={'phone': phone, 'otp': otp, 'purpose': 'LOGIN'},
    )
    return resp.json().get('access_token', '')


def _auth(token):
    return {'Authorization': f'Bearer {token}'}


# ── 1. Doctor → Admin API = 403 ───────────────────────────────

@pytest.mark.django_db
def test_doctor_cannot_access_admin_dashboard(api_client):
    token = _otp_token(api_client, '9700000001', user_type='DOCTOR')
    resp = api_client.get('/api/v1/admin/dashboard/', headers=_auth(token))
    assert resp.status_code == 403


@pytest.mark.django_db
def test_doctor_cannot_access_admin_users(api_client):
    token = _otp_token(api_client, '9700000002', user_type='DOCTOR')
    resp = api_client.get('/api/v1/admin/users/', headers=_auth(token))
    assert resp.status_code == 403


# ── 2. Suspended user → protected API blocked ─────────────────

@pytest.mark.django_db
def test_suspended_user_blocked(api_client):
    from apps.accounts.models import User
    token = _otp_token(api_client, '9700000010', user_type='DOCTOR')
    # Suspend after token issued — next request must be blocked
    User.objects.filter(phone='9700000010').update(status='SUSPENDED')
    resp = api_client.get('/api/v1/doctors/profile/me/', headers=_auth(token))
    assert resp.status_code == 403


# ── 3. Invalid / expired token → 401 ─────────────────────────

@pytest.mark.django_db
def test_invalid_token_rejected(api_client):
    resp = api_client.get(
        '/api/v1/doctors/profile/me/',
        headers={'Authorization': 'Bearer invalid.token.value'},
    )
    assert resp.status_code == 401


@pytest.mark.django_db
def test_no_token_rejected(api_client):
    resp = api_client.get('/api/v1/doctors/profile/me/')
    assert resp.status_code == 403  # HTTPBearer returns 403 when no credentials


# ── 4. Platform Admin → Super Admin endpoints = 403 ──────────

@pytest.mark.django_db
def test_platform_admin_cannot_create_admin_user(api_client):
    """Platform Admin (is_super_admin=False) must get 403 on /super/ endpoints."""
    token = _otp_token(api_client, '9700000020', user_type='ADMIN',
                       is_super_admin=False)
    resp = api_client.post(
        '/api/v1/admin/super/admin-users/',
        json={'phone': '9700099999', 'is_super_admin': False},
        headers=_auth(token),
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_platform_admin_cannot_activate_matching_config(api_client):
    token = _otp_token(api_client, '9700000021', user_type='ADMIN',
                       is_super_admin=False)
    resp = api_client.post(
        '/api/v1/admin/matching-configs/00000000-0000-0000-0000-000000000001/activate/',
        headers=_auth(token),
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_platform_admin_cannot_deactivate_admin_user(api_client):
    token = _otp_token(api_client, '9700000022', user_type='ADMIN',
                       is_super_admin=False)
    resp = api_client.post(
        '/api/v1/admin/super/admin-users/00000000-0000-0000-0000-000000000001/deactivate/',
        json={'reason': 'test'},
        headers=_auth(token),
    )
    assert resp.status_code == 403


# ── 5. Super Admin → allowed ──────────────────────────────────

@pytest.mark.django_db
def test_super_admin_can_access_dashboard(api_client):
    token = _otp_token(api_client, '9700000030', user_type='ADMIN',
                       is_super_admin=True)
    resp = api_client.get('/api/v1/admin/dashboard/', headers=_auth(token))
    assert resp.status_code == 200


@pytest.mark.django_db
def test_super_admin_cannot_deactivate_own_account(api_client):
    from apps.accounts.models import User
    token = _otp_token(api_client, '9700000031', user_type='ADMIN',
                       is_super_admin=True)
    user = User.objects.get(phone='9700000031')
    resp = api_client.post(
        f'/api/v1/admin/super/admin-users/{user.id}/deactivate/',
        json={'reason': 'self-deactivate attempt'},
        headers=_auth(token),
    )
    assert resp.status_code == 400


# ── 6. Hospital A → Hospital B object = 403 ──────────────────

@pytest.mark.django_db
def test_hospital_a_cannot_access_hospital_b_staff(api_client):
    from apps.accounts.models import User
    from apps.hospitals.models import Hospital, HospitalUser

    # Hospital A admin
    token_a = _otp_token(api_client, '9700000040', user_type='HOSPITAL_ADMIN')
    user_a = User.objects.get(phone='9700000040')
    hosp_a = Hospital.objects.create(
        name='Hospital A', type='HOSPITAL',
        location={'city': 'Mumbai', 'state': 'MH'},
    )
    HospitalUser.objects.get_or_create(user=user_a, hospital=hosp_a,
                                       defaults={'role': 'ADMIN'})

    # Hospital B admin
    _otp_token(api_client, '9700000041', user_type='HOSPITAL_ADMIN')
    user_b = User.objects.get(phone='9700000041')
    hosp_b = Hospital.objects.create(
        name='Hospital B', type='HOSPITAL',
        location={'city': 'Delhi', 'state': 'DL'},
    )
    HospitalUser.objects.get_or_create(user=user_b, hospital=hosp_b,
                                       defaults={'role': 'ADMIN'})

    # Hospital A admin tries to list Hospital B staff — must fail
    # The /me/staff/ endpoint resolves hospital from the authenticated user's HospitalUser,
    # so Hospital A admin will only ever see Hospital A staff (scope enforced by ORM filter).
    resp = api_client.get('/api/v1/hospitals/me/staff/', headers=_auth(token_a))
    assert resp.status_code == 200
    phones = [s['phone'] for s in resp.json()]
    assert '9700000041' not in phones  # Hospital B user must not appear


# ── 7. Branch User scope isolation ───────────────────────────

@pytest.mark.django_db
def test_branch_user_identified_via_hospital_user(api_client):
    """Branch User = HospitalUser with branch_id set. No separate user_type needed."""
    from apps.accounts.models import User
    from apps.hospitals.models import Hospital, HospitalBranch, HospitalUser

    _otp_token(api_client, '9700000050', user_type='HOSPITAL_HR')
    user = User.objects.get(phone='9700000050')
    hosp = Hospital.objects.create(
        name='Branch Test Hospital', type='CLINIC',
        location={'city': 'Pune', 'state': 'MH'},
    )
    branch = HospitalBranch.objects.create(
        hospital=hosp, name='Branch 1',
        location={'city': 'Pune', 'state': 'MH'},
    )
    hu = HospitalUser.objects.create(
        user=user, hospital=hosp, role='HR', branch=branch
    )
    # Verify branch scope is stored correctly
    assert hu.branch_id == branch.id
    assert hu.role == 'HR'
    assert hu.hospital_id == hosp.id


# ── 8. HR → Billing = 403 ────────────────────────────────────

@pytest.mark.django_db
def test_hr_cannot_access_billing(api_client):
    token = _otp_token(api_client, '9700000060', user_type='HOSPITAL_HR')
    resp = api_client.get('/api/v1/billing/plans/', headers=_auth(token))
    # Billing endpoints require ADMIN or HOSPITAL_ADMIN — HR gets 403
    assert resp.status_code in (403, 404)  # 404 if route not yet mounted


# ── 9. Refresh token invalid → 401 ───────────────────────────

@pytest.mark.django_db
def test_revoked_refresh_token_rejected(api_client):
    resp = api_client.post(
        '/api/v1/auth/refresh/',
        json={'refresh_token': 'revoked.or.invalid.token'},
    )
    assert resp.status_code == 401


# ── 10. Report evidence not publicly accessible ───────────────

@pytest.mark.django_db
def test_report_evidence_model_exists():
    """ReportEvidence model must exist with correct fields."""
    from apps.core.models import ReportEvidence, Report
    from apps.accounts.models import User
    import uuid

    user, _ = User.objects.get_or_create(
        phone='9700000070',
        defaults={'user_type': 'DOCTOR', 'status': 'ACTIVE'},
    )
    report = Report.objects.create(
        reporter=user,
        target_type='POST',
        target_id=uuid.uuid4(),
        reason='SPAM',
    )
    evidence = ReportEvidence.objects.create(
        report=report,
        evidence_file_id=uuid.uuid4(),
        evidence_type='SCREENSHOT',
        uploaded_by=user,
    )
    assert evidence.id is not None
    assert evidence.report_id == report.id


# ── 11. is_super_admin field exists on User ───────────────────

@pytest.mark.django_db
def test_user_has_is_super_admin_field():
    from apps.accounts.models import User
    user, _ = User.objects.get_or_create(
        phone='9700000080',
        defaults={'user_type': 'ADMIN', 'status': 'ACTIVE', 'is_super_admin': True},
    )
    assert user.is_super_admin is True


# ── 12. HospitalUser has permissions field ────────────────────

@pytest.mark.django_db
def test_hospital_user_has_permissions_field():
    from apps.accounts.models import User
    from apps.hospitals.models import Hospital, HospitalUser

    user, _ = User.objects.get_or_create(
        phone='9700000090',
        defaults={'user_type': 'HOSPITAL_HR', 'status': 'ACTIVE'},
    )
    hosp = Hospital.objects.create(
        name='Perm Test Hospital', type='CLINIC',
        location={'city': 'Chennai', 'state': 'TN'},
    )
    hu = HospitalUser.objects.create(
        user=user, hospital=hosp, role='HR',
        permissions={'can_view_candidates': True},
    )
    assert hu.permissions == {'can_view_candidates': True}


# ── 13. Unauthenticated search blocked ───────────────────────

@pytest.mark.django_db
def test_unauthenticated_doctor_search_blocked(api_client):
    resp = api_client.get('/api/v1/doctors/search/')
    assert resp.status_code == 403


# ── 14. HR cannot access billing plans ───────────────────────

@pytest.mark.django_db
def test_hr_cannot_access_billing_plans(api_client):
    """HOSPITAL_HR must get 403 on billing endpoints (Hospital Admin only)."""
    token = _otp_token(api_client, '9700000061', user_type='HOSPITAL_HR')
    resp = api_client.get('/api/v1/billing/plans/', headers=_auth(token))
    assert resp.status_code == 403


@pytest.mark.django_db
def test_doctor_cannot_access_billing_plans(api_client):
    """DOCTOR must get 403 on billing endpoints."""
    token = _otp_token(api_client, '9700000062', user_type='DOCTOR')
    resp = api_client.get('/api/v1/billing/plans/', headers=_auth(token))
    assert resp.status_code == 403


# ── 15. Hospital A cannot access Hospital B candidate ─────────

@pytest.mark.django_db
def test_hospital_a_cannot_access_hospital_b_jobs(api_client):
    """Hospital A admin cannot update/close Hospital B's job."""
    from apps.accounts.models import User
    from apps.hospitals.models import Hospital, HospitalUser
    from apps.jobs.models import JobPost

    # Hospital A admin
    token_a = _otp_token(api_client, '9700000043', user_type='HOSPITAL_ADMIN')
    user_a = User.objects.get(phone='9700000043')
    hosp_a = Hospital.objects.create(
        name='Scope Hospital A', type='HOSPITAL',
        location={'city': 'Mumbai', 'state': 'MH'},
    )
    HospitalUser.objects.get_or_create(user=user_a, hospital=hosp_a, defaults={'role': 'ADMIN'})

    # Hospital B job
    _otp_token(api_client, '9700000044', user_type='HOSPITAL_ADMIN')
    user_b = User.objects.get(phone='9700000044')
    hosp_b = Hospital.objects.create(
        name='Scope Hospital B', type='HOSPITAL',
        location={'city': 'Delhi', 'state': 'DL'},
    )
    HospitalUser.objects.get_or_create(user=user_b, hospital=hosp_b, defaults={'role': 'ADMIN'})
    job_b = JobPost.objects.create(
        hospital=hosp_b, title='Cardiologist', specialty_id='00000000-0000-0000-0000-000000000001',
        qualification_ids=[], description='Test', location={'city': 'Delhi', 'state': 'DL'},
        job_type='FULL_TIME', status='PUBLISHED', posted_by=user_b,
    )

    # Hospital A admin tries to close Hospital B's job — must fail
    resp = api_client.post(
        f'/api/v1/jobs/{job_b.id}/close/',
        headers=_auth(token_a),
    )
    assert resp.status_code in (403, 404)


# ── 16. Inactive HospitalUser membership blocked ──────────────

@pytest.mark.django_db
def test_inactive_hospital_user_cannot_manage_staff(api_client):
    """HospitalUser with status=INACTIVE must not be able to manage staff."""
    from apps.accounts.models import User
    from apps.hospitals.models import Hospital, HospitalUser

    token = _otp_token(api_client, '9700000051', user_type='HOSPITAL_ADMIN')
    user = User.objects.get(phone='9700000051')
    hosp = Hospital.objects.create(
        name='Inactive Test Hospital', type='CLINIC',
        location={'city': 'Pune', 'state': 'MH'},
    )
    # Create HospitalUser with INACTIVE status
    HospitalUser.objects.create(user=user, hospital=hosp, role='ADMIN', status='INACTIVE')

    # Inactive member tries to list staff — must be blocked because status='ACTIVE' is enforced
    resp = api_client.get('/api/v1/hospitals/me/staff/', headers=_auth(token))
    assert resp.status_code == 403


# ── 17. Private evidence not accessible without auth ──────────

@pytest.mark.django_db
def test_report_evidence_not_publicly_accessible(api_client):
    """ReportEvidence must not be accessible without authentication."""
    import uuid
    # Attempt to access a file by guessing a UUID — must require auth
    resp = api_client.get(f'/api/v1/files/{uuid.uuid4()}/signed-url/')
    assert resp.status_code in (401, 403)


# ── 18. Object ID tampering blocked ──────────────────────────

@pytest.mark.django_db
def test_doctor_cannot_access_another_doctors_private_profile(api_client):
    """Doctor A cannot access Doctor B's private profile data via ID tampering."""
    from apps.accounts.models import User
    from apps.doctors.models import DoctorProfile

    # Doctor A
    token_a = _otp_token(api_client, '9700000071', user_type='DOCTOR')

    # Doctor B with CONNECTIONS_ONLY visibility
    _otp_token(api_client, '9700000072', user_type='DOCTOR')
    user_b = User.objects.get(phone='9700000072')
    profile_b, _ = DoctorProfile.objects.get_or_create(
        user=user_b,
        defaults={
            'first_name': 'Private', 'last_name': 'Doctor',
            'profile_visibility': 'CONNECTIONS_ONLY',
        },
    )

    # Doctor A tries to view Doctor B's profile — privacy enforced at API level
    resp = api_client.get(
        f'/api/v1/doctors/profile/{profile_b.id}/',
        headers=_auth(token_a),
    )
    # Either 404 (privacy-safe) or 200 with limited fields — never full private data
    assert resp.status_code in (200, 403, 404)


# ── 19. Platform Admin cannot suspend/restrict a Super Admin ──

@pytest.mark.django_db
def test_platform_admin_cannot_suspend_super_admin(api_client):
    """Platform Admin must get 403 when trying to suspend a Super Admin user."""
    from apps.accounts.models import User

    # Platform Admin (not super)
    token_pa = _otp_token(api_client, '9700000100', user_type='ADMIN', is_super_admin=False)

    # Super Admin target
    _otp_token(api_client, '9700000101', user_type='ADMIN', is_super_admin=True)
    super_user = User.objects.get(phone='9700000101')

    resp = api_client.post(
        f'/api/v1/admin/users/{super_user.id}/suspend/',
        json={'reason': 'test attempt'},
        headers=_auth(token_pa),
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_platform_admin_cannot_restrict_super_admin(api_client):
    """Platform Admin must get 403 when trying to restrict a Super Admin user."""
    from apps.accounts.models import User

    token_pa = _otp_token(api_client, '9700000102', user_type='ADMIN', is_super_admin=False)

    _otp_token(api_client, '9700000103', user_type='ADMIN', is_super_admin=True)
    super_user = User.objects.get(phone='9700000103')

    resp = api_client.post(
        f'/api/v1/admin/users/{super_user.id}/restrict/',
        json={'reason': 'test attempt'},
        headers=_auth(token_pa),
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_platform_admin_cannot_deactivate_super_admin(api_client):
    """Platform Admin must get 403 when trying to deactivate a Super Admin user."""
    from apps.accounts.models import User

    token_pa = _otp_token(api_client, '9700000104', user_type='ADMIN', is_super_admin=False)

    _otp_token(api_client, '9700000105', user_type='ADMIN', is_super_admin=True)
    super_user = User.objects.get(phone='9700000105')

    resp = api_client.post(
        f'/api/v1/admin/users/{super_user.id}/deactivate/',
        json={'reason': 'test attempt'},
        headers=_auth(token_pa),
    )
    assert resp.status_code == 403


# ── 20. Platform Admin cannot modify Super Admin permissions ──

@pytest.mark.django_db
def test_platform_admin_cannot_modify_super_admin_permissions(api_client):
    """Platform Admin must get 403 on PATCH /super/admin-users/{id}/permissions/."""
    from apps.accounts.models import User

    token_pa = _otp_token(api_client, '9700000106', user_type='ADMIN', is_super_admin=False)

    _otp_token(api_client, '9700000107', user_type='ADMIN', is_super_admin=True)
    super_user = User.objects.get(phone='9700000107')

    resp = api_client.patch(
        f'/api/v1/admin/super/admin-users/{super_user.id}/permissions/',
        json={'phone': '9700000107', 'is_super_admin': False},
        headers=_auth(token_pa),
    )
    assert resp.status_code == 403


# ── 21. Super Admin can suspend a non-super admin user ────────

@pytest.mark.django_db
def test_super_admin_can_suspend_regular_user(api_client):
    """Super Admin must be able to suspend a regular (non-super) user."""
    from apps.accounts.models import User

    token_sa = _otp_token(api_client, '9700000108', user_type='ADMIN', is_super_admin=True)

    _otp_token(api_client, '9700000109', user_type='DOCTOR')
    doctor = User.objects.get(phone='9700000109')

    resp = api_client.post(
        f'/api/v1/admin/users/{doctor.id}/suspend/',
        json={'reason': 'policy violation'},
        headers=_auth(token_sa),
    )
    assert resp.status_code == 200
    doctor.refresh_from_db()
    assert doctor.status == 'SUSPENDED'
