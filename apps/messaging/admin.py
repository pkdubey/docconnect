from django.contrib import messages
from django.contrib.admin import ModelAdmin, TabularInline, action
from apps.core.admin_site import docconnect_admin
from .models import Conversation, ConversationParticipant, Message


class ConversationParticipantInline(TabularInline):
    model = ConversationParticipant
    fields = ('user', 'is_active', 'last_read_at', 'joined_at')
    readonly_fields = ('joined_at',)
    extra = 0


class MessageInline(TabularInline):
    model = Message
    fields = ('sender', 'message_type', 'content', 'created_at')
    readonly_fields = ('created_at',)
    extra = 0
    ordering = ('-created_at',)
    max_num = 20

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@action(description='🚫 Block selected conversations')
def block_conversations(modeladmin, request, queryset):
    # Mark all participants inactive to effectively block
    from apps.core.models import AuditLog
    for conv in queryset:
        conv.participants.update(is_active=False)
        AuditLog.objects.create(
            action='CONVERSATION_BLOCKED',
            target_type='CONVERSATION',
            target_id=conv.id,
            performed_by=request.user,
        )
    messages.warning(request, f'{queryset.count()} conversation(s) blocked.')


class ConversationAdmin(ModelAdmin):
    list_display = ('id', 'type', 'title', 'participant_count', 'created_at')
    list_filter = ('type',)
    search_fields = ('title', 'participants__user__phone')
    ordering = ('-created_at',)
    actions = [block_conversations]
    inlines = [ConversationParticipantInline, MessageInline]

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'


class ConversationParticipantAdmin(ModelAdmin):
    list_display = ('conversation', 'user', 'is_active', 'last_read_at', 'joined_at')
    list_filter = ('is_active',)
    search_fields = ('user__phone',)
    ordering = ('-joined_at',)


class MessageAdmin(ModelAdmin):
    list_display = ('sender', 'conversation', 'message_type', 'created_at')
    list_filter = ('message_type',)
    search_fields = ('sender__phone', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


docconnect_admin.register(Conversation, ConversationAdmin)
docconnect_admin.register(ConversationParticipant, ConversationParticipantAdmin)
docconnect_admin.register(Message, MessageAdmin)
