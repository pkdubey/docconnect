import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = [
        ('DOCTOR', 'Doctor'),
        ('HOSPITAL_ADMIN', 'Hospital Admin'),
        ('HOSPITAL_HR', 'Hospital HR'),
        ('ADMIN', 'Admin'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('DELETED', 'Deleted'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    search_vector = SearchVectorField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['user_type']

    objects = UserManager()

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.phone} ({self.user_type})"


class OTPChallenge(models.Model):
    PURPOSE_CHOICES = [
        ('LOGIN', 'Login'),
        ('REGISTER', 'Register'),
        ('RESET_PASSWORD', 'Reset Password'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=15)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    otp_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)
    resend_count = models.IntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'otp_challenges'
        indexes = [models.Index(fields=['phone', 'purpose'])]

    def __str__(self):
        return f"OTP({self.phone}, {self.purpose})"


class RefreshSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token_hash = models.CharField(max_length=255)
    device_id = models.CharField(max_length=255, null=True, blank=True)
    device_name = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'refresh_sessions'

    def __str__(self):
        return f"Session({self.user.phone})"
