from django.contrib import messages
from django.contrib.admin import ModelAdmin, TabularInline, action
from apps.core.admin_site import docconnect_admin
from .models import Hospital, HospitalBranch, HospitalDepartment, HospitalUser, HospitalFollow


class HospitalBranchInline(TabularInline):
    model = HospitalBranch
    fields = ('name', 'is_primary', 'phone')
    extra = 0


class HospitalDepartmentInline(TabularInline):
    model = HospitalDepartment
    fields = ('name', 'branch', 'active')
    extra = 0


class HospitalUserInline(TabularInline):
    model = HospitalUser
    fields = ('user', 'role', 'designation', 'branch', 'status')
    extra = 0


@action(description='✅ Approve verification')
def approve_hospital(modeladmin, request, queryset):
    from django.utils import timezone
    from apps.core.models import AuditLog
    updated = queryset.exclude(verification_status='VERIFIED').update(
        verification_status='VERIFIED', verified_at=timezone.now()
    )
    for obj in queryset:
        AuditLog.objects.create(
            action='HOSPITAL_VERIFIED',
            target_type='HOSPITAL',
            target_id=obj.id,
            performed_by=request.user,
            metadata={'hospital': obj.name},
        )
    messages.success(request, f'{updated} hospital(s) approved.')


@action(description='❌ Reject verification')
def reject_hospital(modeladmin, request, queryset):
    from apps.core.models import AuditLog
    updated = queryset.exclude(verification_status='REJECTED').update(verification_status='REJECTED')
    for obj in queryset:
        AuditLog.objects.create(
            action='HOSPITAL_REJECTED',
            target_type='HOSPITAL',
            target_id=obj.id,
            performed_by=request.user,
            metadata={'hospital': obj.name},
        )
    messages.warning(request, f'{updated} hospital(s) rejected.')


@action(description='🔴 Suspend selected hospital users')
def suspend_hospital_users(modeladmin, request, queryset):
    from apps.core.models import AuditLog
    qs = queryset.exclude(status='SUSPENDED')
    updated = qs.update(status='SUSPENDED')
    for obj in qs:
        AuditLog.objects.create(
            action='HOSPITAL_USER_SUSPENDED',
            target_type='HOSPITAL_USER',
            target_id=obj.id,
            performed_by=request.user,
            metadata={'user': obj.user.phone, 'hospital': obj.hospital.name},
        )
    messages.warning(request, f'{updated} hospital user(s) suspended.')


@action(description='🟢 Restore selected hospital users')
def restore_hospital_users(modeladmin, request, queryset):
    from apps.core.models import AuditLog
    qs = queryset.exclude(status='ACTIVE')
    updated = qs.update(status='ACTIVE')
    for obj in qs:
        AuditLog.objects.create(
            action='HOSPITAL_USER_RESTORED',
            target_type='HOSPITAL_USER',
            target_id=obj.id,
            performed_by=request.user,
            metadata={'user': obj.user.phone, 'hospital': obj.hospital.name},
        )
    messages.success(request, f'{updated} hospital user(s) restored.')


class HospitalAdmin(ModelAdmin):
    list_display = ('name', 'type', 'verification_status', 'bed_count', 'phone', 'email', 'created_at')
    list_filter = ('type', 'verification_status')
    search_fields = ('name', 'email', 'phone')
    ordering = ('-created_at',)
    exclude = ('metadata', 'logo_base64')
    actions = [approve_hospital, reject_hospital]
    inlines = [HospitalBranchInline, HospitalDepartmentInline, HospitalUserInline]
    fieldsets = (
        ('Hospital Info', {'fields': ('name', 'type', 'about', 'bed_count', 'phone', 'email', 'website', 'location')}),
        ('Verification', {'fields': ('verification_status', 'verified_at')}),
    )
    readonly_fields = ('verified_at',)


class HospitalBranchAdmin(ModelAdmin):
    list_display = ('hospital', 'name', 'is_primary', 'phone')
    search_fields = ('hospital__name', 'name')
    list_filter = ('is_primary',)


class HospitalDepartmentAdmin(ModelAdmin):
    list_display = ('hospital', 'branch', 'name', 'active')
    list_filter = ('active',)
    search_fields = ('hospital__name', 'name')


class HospitalUserAdmin(ModelAdmin):
    list_display = ('get_name', 'user', 'hospital', 'role', 'designation', 'branch', 'status', 'created_at')
    list_filter = ('role', 'status')
    search_fields = ('user__phone', 'hospital__name')
    fields = ('user', 'hospital', 'role', 'designation', 'branch', 'department', 'status', 'permissions')
    actions = [suspend_hospital_users, restore_hospital_users]

    def get_name(self, obj):
        meta = obj.user.metadata or {}
        first = meta.get('first_name', '')
        last = meta.get('last_name', '')
        return f'{first} {last}'.strip() or '—'
    get_name.short_description = 'Name'


class HospitalFollowAdmin(ModelAdmin):
    list_display = ('user', 'hospital', 'created_at')
    search_fields = ('user__phone', 'hospital__name')
    ordering = ('-created_at',)


docconnect_admin.register(Hospital, HospitalAdmin)
docconnect_admin.register(HospitalBranch, HospitalBranchAdmin)
docconnect_admin.register(HospitalDepartment, HospitalDepartmentAdmin)
docconnect_admin.register(HospitalUser, HospitalUserAdmin)
docconnect_admin.register(HospitalFollow, HospitalFollowAdmin)
