import uuid
from django.db import models


class Hospital(models.Model):
    TYPE_CHOICES = [
        ('HOSPITAL', 'Hospital'),
        ('CLINIC', 'Clinic'),
        ('NURSING_HOME', 'Nursing Home'),
        ('MEDICAL_COLLEGE', 'Medical College'),
    ]
    VERIFICATION_STATUS = [
        ('UNVERIFIED', 'Unverified'),
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    logo_file_id = models.UUIDField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    location = models.JSONField()
    bed_count = models.IntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='UNVERIFIED')
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hospitals'

    def __str__(self):
        return self.name


class HospitalBranch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    location = models.JSONField()
    phone = models.CharField(max_length=20, null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hospital_branches'

    def __str__(self):
        return f"{self.hospital.name} — {self.name}"


class HospitalDepartment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='departments')
    branch = models.ForeignKey(HospitalBranch, on_delete=models.CASCADE, null=True, blank=True, related_name='departments')
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hospital_departments'

    def __str__(self):
        return f"{self.hospital.name} / {self.name}"


class HospitalUser(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('HR', 'HR'),
        ('RECRUITER', 'Recruiter'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='hospital_user')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='staff')
    branch = models.ForeignKey(HospitalBranch, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    designation = models.CharField(max_length=100, null=True, blank=True)
    department = models.ForeignKey(HospitalDepartment, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'hospital_users'

    def __str__(self):
        return f"{self.user.phone} @ {self.hospital.name} ({self.role})"
