from django.contrib.admin import ModelAdmin, StackedInline
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.core.admin_site import docconnect_admin
from .models import User, OTPChallenge, RefreshSession


class DoctorProfileInline(StackedInline):
    from apps.doctors.models import DoctorProfile
    model = DoctorProfile
    fields = ('first_name', 'last_name', 'headline', 'experience_years', 'verification_status')
    extra = 0
    can_delete = False
    verbose_name = 'Doctor Profile'


class UserAdmin(BaseUserAdmin):
    list_display = ('phone', 'email', 'get_name', 'user_type', 'status', 'is_staff', 'created_at')
    list_filter = ('user_type', 'status', 'is_staff')
    search_fields = ('phone', 'email')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('phone', 'email', 'password')}),
        ('Info', {'fields': ('user_type', 'status')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions')}),
    )

    def get_inline_instances(self, request, obj=None):
        if obj and obj.user_type == 'DOCTOR':
            return [DoctorProfileInline(self.model, self.admin_site)]
        return []
    add_fieldsets = (
        (None, {'fields': ('phone', 'user_type', 'password1', 'password2')}),
    )

    def get_name(self, obj):
        try:
            dp = obj.doctor_profile
            return f'{dp.first_name} {dp.last_name}'
        except Exception:
            return '—'
    get_name.short_description = 'Name'


class OTPChallengeAdmin(ModelAdmin):
    list_display = ('phone', 'purpose', 'attempts', 'consumed_at', 'expires_at', 'created_at')
    list_filter = ('purpose',)
    search_fields = ('phone',)


class RefreshSessionAdmin(ModelAdmin):
    list_display = ('user', 'device_name', 'ip_address', 'expires_at', 'revoked_at')
    search_fields = ('user__phone',)


docconnect_admin.register(User, UserAdmin)
docconnect_admin.register(OTPChallenge, OTPChallengeAdmin)
docconnect_admin.register(RefreshSession, RefreshSessionAdmin)
