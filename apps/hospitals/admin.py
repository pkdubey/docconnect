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
    list_display = ('user', 'hospital', 'role', 'status', 'created_at')
    list_filter = ('role', 'status')
    search_fields = ('user__phone', 'hospital__name')


docconnect_admin.register(Hospital, HospitalAdmin)
docconnect_admin.register(HospitalBranch, HospitalBranchAdmin)
docconnect_admin.register(HospitalDepartment, HospitalDepartmentAdmin)
docconnect_admin.register(HospitalUser, HospitalUserAdmin)
