import uuid
from django.db import models


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    body = models.TextField(null=True, blank=True)
    data_json = models.JSONField(null=True, blank=True)
    deep_link = models.CharField(max_length=255, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        indexes = [models.Index(fields=['user', 'is_read'])]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.phone} — {self.title}"


class DeviceToken(models.Model):
    """Push notification device tokens (FCM/APNs)."""
    PLATFORM_CHOICES = [
        ('FCM', 'FCM (Android/Firebase)'),
        ('APNS', 'APNs (iOS)'),
        ('WEB', 'Web'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='device_tokens')
    token = models.TextField(unique=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, default='FCM')
    device_id = models.CharField(max_length=255, null=True, blank=True)
    device_name = models.CharField(max_length=255, null=True, blank=True)
    bundle_id = models.CharField(max_length=255, null=True, blank=True)  # iOS APNs bundle ID
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'device_tokens'
        indexes = [models.Index(fields=['user', 'is_active'])]

    def __str__(self):
        return f"{self.user.phone} [{self.platform}]"


class NotificationPreference(models.Model):
    """Per-user, per-event notification channel preferences."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='notification_preferences')
    # Each field: True = enabled for that channel
    connection_request_push = models.BooleanField(default=True)
    connection_request_inapp = models.BooleanField(default=True)
    post_interaction_push = models.BooleanField(default=True)
    post_interaction_inapp = models.BooleanField(default=True)
    new_message_push = models.BooleanField(default=True)
    new_message_inapp = models.BooleanField(default=True)
    job_recommendation_push = models.BooleanField(default=True)
    job_recommendation_inapp = models.BooleanField(default=True)
    application_update_push = models.BooleanField(default=True)
    application_update_inapp = models.BooleanField(default=True)
    shift_request_push = models.BooleanField(default=True)
    shift_request_inapp = models.BooleanField(default=True)
    verification_update_push = models.BooleanField(default=True)
    verification_update_inapp = models.BooleanField(default=True)
    # Catch-all JSONB for future event types without schema changes
    extra = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preferences'

    def __str__(self):
        return f"Prefs({self.user.phone})"
