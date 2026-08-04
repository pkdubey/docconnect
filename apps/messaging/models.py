import uuid
from django.db import models


class Conversation(models.Model):
    TYPE = [
        ('DIRECT', 'Direct'),
        ('GROUP', 'Group'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=20, choices=TYPE)
    title = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conversations'

    def __str__(self):
        return f"{self.type} — {self.id}"


class ConversationParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='conversations')
    last_read_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'conversation_participants'
        unique_together = ('conversation', 'user')

    def __str__(self):
        return f"{self.user.phone} in {self.conversation_id}"


class Message(models.Model):
    MESSAGE_TYPE = [
        ('TEXT', 'Text'),
        ('IMAGE', 'Image'),
        ('DOCUMENT', 'Document'),
        ('SHIFT_REQUEST', 'Shift Request'),
        ('JOB_REFERRAL', 'Job Referral'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(null=True, blank=True)
    file_id = models.UUIDField(null=True, blank=True)
    file_type = models.CharField(max_length=50, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE, default='TEXT')
    metadata = models.JSONField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.phone}: {self.message_type}"
