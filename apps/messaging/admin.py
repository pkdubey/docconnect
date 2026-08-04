from django.contrib.admin import ModelAdmin
from apps.core.admin_site import docconnect_admin
from .models import Conversation, ConversationParticipant, Message


class ConversationAdmin(ModelAdmin):
    list_display = ('id', 'type', 'title', 'created_at')
    list_filter = ('type',)


class ConversationParticipantAdmin(ModelAdmin):
    list_display = ('conversation', 'user', 'is_active', 'joined_at')
    search_fields = ('user__phone',)


class MessageAdmin(ModelAdmin):
    list_display = ('sender', 'conversation', 'message_type', 'created_at')
    list_filter = ('message_type',)
    search_fields = ('sender__phone',)


docconnect_admin.register(Conversation, ConversationAdmin)
docconnect_admin.register(ConversationParticipant, ConversationParticipantAdmin)
docconnect_admin.register(Message, MessageAdmin)
