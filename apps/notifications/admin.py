from django.contrib.admin import ModelAdmin
from apps.core.admin_site import docconnect_admin
from .models import Notification


class NotificationAdmin(ModelAdmin):
    list_display = ('user', 'type', 'title', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')
    search_fields = ('user__phone', 'title')


docconnect_admin.register(Notification, NotificationAdmin)
