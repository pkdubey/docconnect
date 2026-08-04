import uuid
from django.db import models


class DoctorAvailability(models.Model):
    AVAILABILITY_TYPE = [
        ('LOCUM', 'Locum'),
        ('VISITING', 'Visiting'),
        ('TEMPORARY', 'Temporary'),
        ('PART_TIME', 'Part Time'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey('doctors.DoctorProfile', on_delete=models.CASCADE, related_name='availabilities')
    availability_type = models.CharField(max_length=20, choices=AVAILABILITY_TYPE)
    available_from = models.DateField()
    available_until = models.DateField()
    preferred_location = models.JSONField(null=True, blank=True)
    preferred_radius_km = models.IntegerField(null=True, blank=True)
    minimum_compensation = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='INR')
    notes = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doctor_availabilities'

    def __str__(self):
        return f"{self.doctor} — {self.availability_type} ({self.available_from} to {self.available_until})"


class AvailabilitySlot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    availability = models.ForeignKey(DoctorAvailability, on_delete=models.CASCADE, related_name='slots')
    slot_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'availability_slots'
        constraints = [
            models.CheckConstraint(check=models.Q(end_time__gt=models.F('start_time')), name='slot_end_after_start')
        ]

    def __str__(self):
        return f"{self.slot_date} {self.start_time}–{self.end_time}"
