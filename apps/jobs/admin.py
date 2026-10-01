from django.contrib import messages
from django.contrib.admin import ModelAdmin, TabularInline, action
from django.utils import timezone
from apps.core.admin_site import docconnect_admin
from .models import JobPost, JobApplication, ApplicationHistory, JobSave


# ── Job Actions ───────────────────────────────────────────────

@action(description='📢 Publish selected jobs')
def publish_jobs(modeladmin, request, queryset):
    qs = queryset.filter(status='DRAFT')
    updated = qs.update(status='PUBLISHED', published_at=timezone.now())
    messages.success(request, f'{updated} job(s) published.')


@action(description='🔒 Close selected jobs')
def close_jobs(modeladmin, request, queryset):
    updated = queryset.filter(status='PUBLISHED').update(status='CLOSED')
    messages.warning(request, f'{updated} job(s) closed.')


@action(description='✅ Mark selected jobs as Filled')
def mark_jobs_filled(modeladmin, request, queryset):
    updated = queryset.filter(status='PUBLISHED').update(status='FILLED')
    messages.success(request, f'{updated} job(s) marked as filled.')


@action(description='⏰ Mark selected jobs as Expired')
def mark_jobs_expired(modeladmin, request, queryset):
    updated = queryset.filter(status='PUBLISHED').update(status='EXPIRED')
    messages.info(request, f'{updated} job(s) marked as expired.')


@action(description='🚫 Remove (policy violation)')
def remove_jobs(modeladmin, request, queryset):
    from apps.core.models import AuditLog
    qs = queryset.exclude(status='CLOSED')
    updated = qs.update(status='CLOSED')
    for obj in qs:
        AuditLog.objects.create(
            action='JOB_REMOVED_POLICY_VIOLATION',
            target_type='JOB',
            target_id=obj.id,
            performed_by=request.user,
            metadata={'title': obj.title, 'hospital': obj.hospital.name},
        )
    messages.error(request, f'{updated} job(s) removed for policy violation.')


# ── Application Actions (README §3.3 full pipeline) ──────────

@action(description='👁 Mark as Profile Viewed')
def mark_profile_viewed(modeladmin, request, queryset):
    _update_application_status(request, queryset, 'PROFILE_VIEWED')


@action(description='⭐ Shortlist selected applications')
def shortlist_applications(modeladmin, request, queryset):
    _update_application_status(request, queryset, 'SHORTLISTED')


@action(description='📅 Move to Interview stage')
def move_to_interview(modeladmin, request, queryset):
    _update_application_status(request, queryset, 'INTERVIEW')


@action(description='📄 Mark as Offered')
def mark_offered(modeladmin, request, queryset):
    _update_application_status(request, queryset, 'OFFERED')


@action(description='✅ Mark as Hired')
def mark_hired(modeladmin, request, queryset):
    _update_application_status(request, queryset, 'HIRED')


@action(description='❌ Reject selected applications')
def reject_applications(modeladmin, request, queryset):
    _update_application_status(request, queryset, 'REJECTED')


def _update_application_status(request, queryset, new_status):
    for obj in queryset:
        old_status = obj.status
        if old_status != new_status:
            obj.status = new_status
            obj.save(update_fields=['status', 'updated_at'])
            ApplicationHistory.objects.create(
                application=obj,
                from_status=old_status,
                to_status=new_status,
                changed_by=request.user,
                notes=f'Bulk action by admin {request.user.phone}',
            )
    messages.success(request, f'{queryset.count()} application(s) updated to {new_status}.')


# ── Inlines ───────────────────────────────────────────────────

class ApplicationHistoryInline(TabularInline):
    model = ApplicationHistory
    fields = ('from_status', 'to_status', 'changed_by', 'notes', 'created_at')
    readonly_fields = ('created_at',)
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class JobApplicationInline(TabularInline):
    model = JobApplication
    fields = ('doctor', 'status', 'applied_at')
    readonly_fields = ('applied_at',)
    extra = 0
    show_change_link = True


# ── Admins ────────────────────────────────────────────────────

class JobPostAdmin(ModelAdmin):
    list_display = ('title', 'hospital', 'job_type', 'status', 'is_urgent', 'positions', 'experience_min_years', 'published_at', 'closing_date')
    list_filter = ('job_type', 'status', 'is_urgent', 'shift_type', 'salary_visibility')
    search_fields = ('title', 'hospital__name')
    ordering = ('-created_at',)
    exclude = ('metadata', 'search_vector')
    actions = [publish_jobs, close_jobs, mark_jobs_filled, mark_jobs_expired, remove_jobs]
    inlines = [JobApplicationInline]
    fieldsets = (
        ('Job Info', {'fields': ('hospital', 'branch', 'department', 'title', 'description', 'responsibilities', 'requirements')}),
        ('Requirements', {'fields': ('specialty_id', 'qualification_ids', 'experience_min_years', 'experience_max_years')}),
        ('Details', {'fields': ('job_type', 'shift_type', 'positions', 'is_urgent', 'joining_requirement', 'location')}),
        ('Salary', {'fields': ('salary_min', 'salary_max', 'salary_visibility', 'currency')}),
        ('Status', {'fields': ('status', 'posted_by', 'published_at', 'closing_date')}),
    )


class JobApplicationAdmin(ModelAdmin):
    list_display = ('doctor', 'job', 'status', 'applied_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('doctor__first_name', 'doctor__last_name', 'job__title', 'job__hospital__name')
    ordering = ('-applied_at',)
    actions = [mark_profile_viewed, shortlist_applications, move_to_interview, mark_offered, mark_hired, reject_applications]
    inlines = [ApplicationHistoryInline]
    readonly_fields = ('applied_at',)


class ApplicationHistoryAdmin(ModelAdmin):
    list_display = ('application', 'from_status', 'to_status', 'changed_by', 'notes', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    search_fields = ('application__doctor__first_name', 'application__job__title')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class JobSaveAdmin(ModelAdmin):
    list_display = ('doctor', 'job', 'created_at')
    search_fields = ('doctor__first_name', 'job__title')
    ordering = ('-created_at',)


docconnect_admin.register(JobPost, JobPostAdmin)
docconnect_admin.register(JobApplication, JobApplicationAdmin)
docconnect_admin.register(ApplicationHistory, ApplicationHistoryAdmin)
docconnect_admin.register(JobSave, JobSaveAdmin)
