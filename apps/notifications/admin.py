from django.contrib.admin import ModelAdmin
from apps.core.admin_site import docconnect_admin
from .models import Notification, DeviceToken, NotificationPreference


class NotificationAdmin(ModelAdmin):
    list_display = ('user', 'type', 'title', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')
    search_fields = ('user__phone', 'title')
    ordering = ('-created_at',)


class DeviceTokenAdmin(ModelAdmin):
    list_display = ('user', 'platform', 'device_name', 'is_active', 'created_at')
    list_filter = ('platform', 'is_active')
    search_fields = ('user__phone', 'device_name')
    ordering = ('-created_at',)


class NotificationPreferenceAdmin(ModelAdmin):
    list_display = ('user', 'connection_request_push', 'new_message_push', 'job_recommendation_push', 'shift_request_push')
    search_fields = ('user__phone',)


docconnect_admin.register(Notification, NotificationAdmin)
docconnect_admin.register(DeviceToken, DeviceTokenAdmin)
docconnect_admin.register(NotificationPreference, NotificationPreferenceAdmin)
