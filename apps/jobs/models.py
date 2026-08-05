import uuid
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchVectorField
from django.db import models


class JobPost(models.Model):
    JOB_TYPE = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('VISITING', 'Visiting'),
        ('LOCUM', 'Locum'),
        ('CONTRACT', 'Contract'),
    ]
    SHIFT_TYPE = [
        ('DAY', 'Day'),
        ('NIGHT', 'Night'),
        ('ROTATIONAL', 'Rotational'),
        ('FLEXIBLE', 'Flexible'),
    ]
    SALARY_VISIBILITY = [
        ('PUBLIC', 'Public'),
        ('ON_REQUEST', 'On Request'),
        ('HIDDEN', 'Hidden'),
    ]
    STATUS = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('CLOSED', 'Closed'),
        ('EXPIRED', 'Expired'),
        ('FILLED', 'Filled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey('hospitals.Hospital', on_delete=models.CASCADE, related_name='job_posts')
    branch = models.ForeignKey('hospitals.HospitalBranch', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey('hospitals.HospitalDepartment', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=160)
    specialty_id = models.UUIDField()
    qualification_ids = ArrayField(models.UUIDField())
    description = models.TextField()
    responsibilities = models.TextField(null=True, blank=True)
    requirements = models.TextField(null=True, blank=True)
    location = models.JSONField()
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_visibility = models.CharField(max_length=20, choices=SALARY_VISIBILITY, default='PUBLIC')
    currency = models.CharField(max_length=3, default='INR')
    job_type = models.CharField(max_length=20, choices=JOB_TYPE)
    experience_min_years = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    experience_max_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPE, default='DAY')
    joining_requirement = models.CharField(max_length=50, null=True, blank=True)
    positions = models.IntegerField(default=1)
    is_urgent = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS, default='DRAFT')
    posted_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    published_at = models.DateTimeField(null=True, blank=True)
    closing_date = models.DateTimeField(null=True, blank=True)
    search_vector = SearchVectorField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'job_posts'
        indexes = [
            models.Index(fields=['hospital', 'status']),
            models.Index(fields=['specialty_id', 'status']),
        ]

    def __str__(self):
        return f"{self.title} @ {self.hospital.name}"


class JobApplication(models.Model):
    STATUS = [
        ('APPLIED', 'Applied'),
        ('PROFILE_VIEWED', 'Profile Viewed'),
        ('SHORTLISTED', 'Shortlisted'),
        ('INTERVIEW', 'Interview'),
        ('OFFERED', 'Offered'),
        ('HIRED', 'Hired'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='applications')
    doctor = models.ForeignKey('doctors.DoctorProfile', on_delete=models.CASCADE, related_name='applications')
    cv_file_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='APPLIED')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'job_applications'
        unique_together = ('job', 'doctor')
        indexes = [models.Index(fields=['job', 'status'])]

    def __str__(self):
        return f"{self.doctor} → {self.job.title}"


class ApplicationHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='history')
    from_status = models.CharField(max_length=20, null=True, blank=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'application_histories'

    def __str__(self):
        return f"{self.from_status} → {self.to_status}"
