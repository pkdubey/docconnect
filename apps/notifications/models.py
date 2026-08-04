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
