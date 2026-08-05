from django.contrib.admin import ModelAdmin
from apps.core.admin_site import docconnect_admin
from .models import JobPost, JobApplication, ApplicationHistory


class JobPostAdmin(ModelAdmin):
    list_display = ('title', 'hospital', 'job_type', 'status', 'is_urgent', 'published_at')
    list_filter = ('job_type', 'status', 'is_urgent', 'shift_type')
    search_fields = ('title', 'hospital__name')
    ordering = ('-created_at',)
    exclude = ('metadata', 'search_vector')


class JobApplicationAdmin(ModelAdmin):
    list_display = ('doctor', 'job', 'status', 'applied_at')
    list_filter = ('status',)
    search_fields = ('doctor__first_name', 'job__title')


class ApplicationHistoryAdmin(ModelAdmin):
    list_display = ('application', 'from_status', 'to_status', 'changed_by', 'created_at')


docconnect_admin.register(JobPost, JobPostAdmin)
docconnect_admin.register(JobApplication, JobApplicationAdmin)
docconnect_admin.register(ApplicationHistory, ApplicationHistoryAdmin)
