from django import forms
from django.contrib.admin import ModelAdmin, StackedInline
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.core.admin_site import docconnect_admin
from .models import User, OTPChallenge, RefreshSession


class UserChangeForm(forms.ModelForm):
    first_name = forms.CharField(max_length=80, required=False, label='First Name')
    last_name = forms.CharField(max_length=80, required=False, label='Last Name')

    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            meta = self.instance.metadata or {}
            # For doctors, pull from DoctorProfile
            if self.instance.user_type == 'DOCTOR':
                try:
                    dp = self.instance.doctor_profile
                    self.fields['first_name'].initial = dp.first_name
                    self.fields['last_name'].initial = dp.last_name
                except Exception:
                    pass
            else:
                self.fields['first_name'].initial = meta.get('first_name', '')
                self.fields['last_name'].initial = meta.get('last_name', '')

    def save(self, commit=True):
        user = super().save(commit=False)
        first = self.cleaned_data.get('first_name', '').strip()
        last = self.cleaned_data.get('last_name', '').strip()
        if user.user_type == 'DOCTOR':
            try:
                dp = user.doctor_profile
                if first:
                    dp.first_name = first
                if last:
                    dp.last_name = last
                dp.save(update_fields=['first_name', 'last_name'])
            except Exception:
                pass
        else:
            meta = user.metadata or {}
            meta['first_name'] = first
            meta['last_name'] = last
            user.metadata = meta
        if commit:
            user.save()
        return user


class DoctorProfileInline(StackedInline):
    from apps.doctors.models import DoctorProfile
    model = DoctorProfile
    fields = ('first_name', 'last_name', 'headline', 'experience_years', 'verification_status')
    extra = 0
    can_delete = False
    verbose_name = 'Doctor Profile'


class HospitalUserInline(StackedInline):
    from apps.hospitals.models import HospitalUser
    model = HospitalUser
    fields = ('hospital', 'role', 'designation', 'status')
    extra = 0
    can_delete = False
    verbose_name = 'Hospital Association'


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    list_display = ('phone', 'email', 'get_name', 'user_type', 'status', 'is_staff', 'created_at')
    list_filter = ('user_type', 'status', 'is_staff')
    search_fields = ('phone', 'email')
    ordering = ('-created_at',)
    exclude = ('search_vector', 'metadata')
    fieldsets = (
        (None, {'fields': ('phone', 'email', 'password')}),
        ('Name', {'fields': ('first_name', 'last_name')}),
        ('Info', {'fields': ('user_type', 'status')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'fields': ('phone', 'user_type', 'password1', 'password2')}),
    )

    def get_inline_instances(self, request, obj=None):
        if obj and obj.user_type == 'DOCTOR':
            return [DoctorProfileInline(self.model, self.admin_site)]
        if obj and obj.user_type in ('HOSPITAL_ADMIN', 'HOSPITAL_HR'):
            return [HospitalUserInline(self.model, self.admin_site)]
        return []

    def get_name(self, obj):
        try:
            if obj.user_type == 'DOCTOR':
                dp = obj.doctor_profile
                return f'{dp.first_name} {dp.last_name}'
        except Exception:
            pass
        meta = obj.metadata or {}
        first = meta.get('first_name', '')
        last = meta.get('last_name', '')
        return f'{first} {last}'.strip() or '—'
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
