import uuid
from django.contrib.postgres.fields import ArrayField
from django.db import models


class ShiftRequirement(models.Model):
    URGENCY = [
        ('NORMAL', 'Normal'),
        ('URGENT', 'Urgent'),
        ('IMMEDIATE', 'Immediate'),
    ]
    STATUS = [
        ('OPEN', 'Open'),
        ('FILLED', 'Filled'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey('hospitals.Hospital', on_delete=models.CASCADE, related_name='shift_requirements')
    branch = models.ForeignKey('hospitals.HospitalBranch', on_delete=models.SET_NULL, null=True, blank=True)
    specialty_id = models.UUIDField()
    qualification_ids = ArrayField(models.UUIDField())
    requirement_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.JSONField()
    compensation = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    doctors_required = models.IntegerField(default=1)
    urgency = models.CharField(max_length=20, choices=URGENCY, default='NORMAL')
    notes = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='OPEN')
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shift_requirements'
        indexes = [models.Index(fields=['hospital', 'status'])]

    def __str__(self):
        return f"{self.hospital.name} — {self.requirement_date} ({self.urgency})"


class ShiftRequest(models.Model):
    STATUS = [
        ('REQUESTED', 'Requested'),
        ('ACCEPTED_BY_DOCTOR', 'Accepted by Doctor'),
        ('DECLINED_BY_DOCTOR', 'Declined by Doctor'),
        ('CONFIRMED_BY_HOSPITAL', 'Confirmed by Hospital'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement = models.ForeignKey(ShiftRequirement, on_delete=models.CASCADE, related_name='requests')
    doctor = models.ForeignKey('doctors.DoctorProfile', on_delete=models.CASCADE, related_name='shift_requests')
    status = models.CharField(max_length=30, choices=STATUS, default='REQUESTED')
    requested_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'shift_requests'
        unique_together = ('requirement', 'doctor')

    def __str__(self):
        return f"{self.doctor} → {self.requirement} ({self.status})"
