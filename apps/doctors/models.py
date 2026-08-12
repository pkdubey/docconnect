import uuid
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchVectorField
from django.db import models


class DoctorProfile(models.Model):
    VERIFICATION_STATUS = [
        ('UNVERIFIED', 'Unverified'),
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]
    PROFILE_VISIBILITY = [
        ('EVERYONE', 'Everyone'),
        ('DOCTORS_ONLY', 'Doctors Only'),
        ('CONNECTIONS_ONLY', 'Connections Only'),
    ]
    CAREER_VISIBILITY = [
        ('VERIFIED_HOSPITALS', 'Verified Hospitals'),
        ('SELECTED_HOSPITALS', 'Selected Hospitals'),
        ('HIDDEN', 'Hidden'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        'accounts.User', on_delete=models.CASCADE, related_name='doctor_profile'
    )
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    photo_file_id = models.UUIDField(null=True, blank=True)
    photo_base64 = models.TextField(null=True, blank=True)
    cover_base64 = models.TextField(null=True, blank=True)
    headline = models.CharField(max_length=160, null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    primary_specialization_id = models.UUIDField(null=True, blank=True)
    clinical_interests = ArrayField(models.UUIDField(), default=list, blank=True)
    professional_location = models.JSONField(default=dict, blank=True)
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    open_to_opportunities = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20, choices=VERIFICATION_STATUS, default='UNVERIFIED'
    )
    verification_rejected_reason = models.TextField(null=True, blank=True)
    profile_visibility = models.CharField(
        max_length=20, choices=PROFILE_VISIBILITY, default='EVERYONE'
    )
    career_visibility = models.CharField(
        max_length=20, choices=CAREER_VISIBILITY, default='VERIFIED_HOSPITALS'
    )
    search_vector = SearchVectorField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doctor_profiles'

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_verified(self):
        return self.verification_status == 'VERIFIED'

    def __str__(self):
        return self.full_name


class DoctorRegistration(models.Model):
    VERIFICATION_STATUS = [
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='registrations')
    council_id = models.UUIDField()
    registration_number = models.CharField(max_length=50)
    registration_year = models.IntegerField()
    is_primary = models.BooleanField(default=True)
    verification_status = models.CharField(
        max_length=20, choices=VERIFICATION_STATUS, default='PENDING'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doctor_registrations'
        unique_together = ('council_id', 'registration_number')

    def __str__(self):
        return f"{self.registration_number}"


class DoctorQualification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='qualifications')
    degree = models.CharField(max_length=100)
    institution = models.CharField(max_length=255)
    year = models.IntegerField()
    specialization = models.CharField(max_length=100, null=True, blank=True)
    file_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doctor_qualifications'

    def __str__(self):
        return f"{self.degree} — {self.institution}"


class Connection(models.Model):
    STATUS = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
        ('WITHDRAWN', 'Withdrawn'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name='sent_connections'
    )
    receiver = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name='received_connections'
    )
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doctor_connections'
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.status})"


class DoctorExperience(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='experiences')
    role = models.CharField(max_length=100)
    hospital_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doctor_experiences'

    def __str__(self):
        return f"{self.role} @ {self.hospital_name}"


class Post(models.Model):
    POST_TYPES = [
        ('UPDATE', 'Update'),
        ('CASE', 'Clinical Case'),
        ('ARTICLE', 'Article'),
        ('PHOTO', 'Photo'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # doctor author (null for hospital/admin posts)
    author = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    # always set — the user who created the post
    posted_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='UPDATE')
    content = models.TextField()
    image_base64 = models.TextField(null=True, blank=True)
    is_anonymous = models.BooleanField(default=False)  # for case discussions
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'doctor_posts'
        ordering = ['-created_at']

    @property
    def display_name(self):
        if self.is_anonymous:
            return 'Anonymous'
        if self.author:
            return f'Dr. {self.author.full_name}'
        if self.posted_by:
            if self.posted_by.user_type in ('HOSPITAL_ADMIN', 'HOSPITAL_HR'):
                try:
                    from apps.hospitals.models import HospitalUser
                    hu = HospitalUser.objects.select_related('hospital').get(user=self.posted_by)
                    return hu.hospital.name
                except Exception:
                    pass
            # ADMIN / superuser — use metadata name, else "DocConnect Team"
            meta = self.posted_by.metadata or {}
            first = meta.get('first_name', '').strip()
            last = meta.get('last_name', '').strip()
            if first or last:
                return f'{first} {last}'.strip()
            return 'DocConnect Team'
        return 'DocConnect Team'

    def __str__(self):
        return f"{self.display_name} — {self.post_type}"


class PostLike(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='liked_posts')
    liked_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='post_likes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post_likes'
        unique_together = ('post', 'liked_by')


class PostComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='post_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post_comments'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author} on {self.post_id}"
