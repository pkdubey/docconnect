from django.contrib import messages
from django.contrib.admin import ModelAdmin, TabularInline, action
from django.utils import timezone
from apps.core.admin_site import docconnect_admin
from .models import ShiftRequirement, ShiftRequest, ShiftStatusHistory


class ShiftRequestInline(TabularInline):
    model = ShiftRequest
    fields = ('doctor', 'status', 'requested_at')
    readonly_fields = ('requested_at',)
    extra = 0


class ShiftStatusHistoryInline(TabularInline):
    model = ShiftStatusHistory
    fields = ('from_status', 'to_status', 'changed_by', 'notes', 'created_at')
    readonly_fields = ('created_at',)
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ── Shift Requirement Actions ────────────────────────────────────

@action(description='❌ Cancel selected requirements')
def cancel_requirements(modeladmin, request, queryset):
    updated = queryset.filter(status='OPEN').update(status='CANCELLED')
    messages.warning(request, f'{updated} requirement(s) cancelled.')


@action(description='✅ Mark as Filled')
def mark_filled(modeladmin, request, queryset):
    updated = queryset.filter(status='OPEN').update(status='FILLED')
    messages.success(request, f'{updated} requirement(s) marked as filled.')


# ── Shift Request Actions (README §4.4 lifecycle) ─────────────────

def _log_shift_transition(request, obj, new_status):
    ShiftStatusHistory.objects.create(
        shift_request=obj,
        from_status=obj.status,
        to_status=new_status,
        changed_by=request.user,
        notes=f'Admin bulk action by {request.user.phone}',
    )


@action(description='✅ Confirm selected shift requests')
def confirm_shifts(modeladmin, request, queryset):
    qs = queryset.filter(status='ACCEPTED_BY_DOCTOR')
    for obj in qs:
        _log_shift_transition(request, obj, 'CONFIRMED_BY_HOSPITAL')
        obj.status = 'CONFIRMED_BY_HOSPITAL'
        obj.confirmed_at = timezone.now()
        obj.save(update_fields=['status', 'confirmed_at'])
    messages.success(request, f'{qs.count()} shift(s) confirmed.')


@action(description='🏁 Mark shifts as Completed')
def complete_shifts(modeladmin, request, queryset):
    qs = queryset.filter(status='CONFIRMED_BY_HOSPITAL')
    for obj in qs:
        _log_shift_transition(request, obj, 'COMPLETED')
        obj.status = 'COMPLETED'
        obj.completed_at = timezone.now()
        obj.save(update_fields=['status', 'completed_at'])
    messages.success(request, f'{qs.count()} shift(s) marked completed.')


@action(description='❌ Cancel selected shift requests')
def cancel_shifts(modeladmin, request, queryset):
    qs = queryset.exclude(status__in=['COMPLETED', 'CANCELLED'])
    for obj in qs:
        _log_shift_transition(request, obj, 'CANCELLED')
        obj.status = 'CANCELLED'
        obj.cancelled_at = timezone.now()
        obj.save(update_fields=['status', 'cancelled_at'])
    messages.warning(request, f'{qs.count()} shift request(s) cancelled.')


class ShiftRequirementAdmin(ModelAdmin):
    list_display = ('hospital', 'requirement_date', 'start_time', 'end_time', 'urgency', 'status', 'doctors_required', 'compensation')
    list_filter = ('urgency', 'status')
    search_fields = ('hospital__name',)
    ordering = ('-created_at',)
    actions = [cancel_requirements, mark_filled]
    inlines = [ShiftRequestInline]


class ShiftRequestAdmin(ModelAdmin):
    list_display = ('doctor', 'requirement', 'status', 'requested_at', 'confirmed_at', 'completed_at', 'cancelled_at')
    list_filter = ('status',)
    search_fields = ('doctor__first_name', 'doctor__last_name', 'requirement__hospital__name')
    ordering = ('-requested_at',)
    actions = [confirm_shifts, complete_shifts, cancel_shifts]
    inlines = [ShiftStatusHistoryInline]


class ShiftStatusHistoryAdmin(ModelAdmin):
    list_display = ('shift_request', 'from_status', 'to_status', 'changed_by', 'created_at')
    readonly_fields = ('shift_request', 'from_status', 'to_status', 'changed_by', 'notes', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


docconnect_admin.register(ShiftRequirement, ShiftRequirementAdmin)
docconnect_admin.register(ShiftRequest, ShiftRequestAdmin)
docconnect_admin.register(ShiftStatusHistory, ShiftStatusHistoryAdmin)
