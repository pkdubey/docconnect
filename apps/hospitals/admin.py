from django.contrib.admin import ModelAdmin
from apps.core.admin_site import docconnect_admin
from .models import Hospital, HospitalBranch, HospitalDepartment, HospitalUser


class HospitalAdmin(ModelAdmin):
    list_display = ('name', 'type', 'verification_status', 'bed_count', 'created_at')
    list_filter = ('type', 'verification_status')
    search_fields = ('name', 'email', 'phone')
    ordering = ('-created_at',)


class HospitalBranchAdmin(ModelAdmin):
    list_display = ('hospital', 'name', 'is_primary', 'phone')
    search_fields = ('hospital__name', 'name')


class HospitalDepartmentAdmin(ModelAdmin):
    list_display = ('hospital', 'branch', 'name', 'active')
    list_filter = ('active',)
    search_fields = ('hospital__name', 'name')


class HospitalUserAdmin(ModelAdmin):
    list_display = ('get_name', 'user', 'hospital', 'role', 'designation', 'status', 'created_at')
    list_filter = ('role', 'status')
    search_fields = ('user__phone', 'hospital__name')
    fields = ('user', 'hospital', 'role', 'designation', 'branch', 'department', 'status')

    def get_name(self, obj):
        meta = obj.user.metadata or {}
        first = meta.get('first_name', '')
        last = meta.get('last_name', '')
        return f'{first} {last}'.strip() or '—'
    get_name.short_description = 'Name'


docconnect_admin.register(Hospital, HospitalAdmin)
docconnect_admin.register(HospitalBranch, HospitalBranchAdmin)
docconnect_admin.register(HospitalDepartment, HospitalDepartmentAdmin)
docconnect_admin.register(HospitalUser, HospitalUserAdmin)
