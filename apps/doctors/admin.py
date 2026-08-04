from django.contrib.admin import ModelAdmin
from apps.core.admin_site import docconnect_admin
from .models import DoctorProfile, DoctorRegistration, DoctorQualification, DoctorExperience


class DoctorProfileAdmin(ModelAdmin):
    list_display = ('full_name', 'user', 'verification_status', 'experience_years', 'created_at')
    list_filter = ('verification_status', 'profile_visibility')
    search_fields = ('first_name', 'last_name', 'user__phone')
    ordering = ('-created_at',)


class DoctorRegistrationAdmin(ModelAdmin):
    list_display = ('doctor', 'registration_number', 'registration_year', 'verification_status')
    list_filter = ('verification_status',)
    search_fields = ('registration_number', 'doctor__first_name')


class DoctorQualificationAdmin(ModelAdmin):
    list_display = ('doctor', 'degree', 'institution', 'year')
    search_fields = ('doctor__first_name', 'degree', 'institution')


class DoctorExperienceAdmin(ModelAdmin):
    list_display = ('doctor', 'role', 'hospital_name', 'start_date', 'is_current')
    search_fields = ('doctor__first_name', 'hospital_name')


docconnect_admin.register(DoctorProfile, DoctorProfileAdmin)
docconnect_admin.register(DoctorRegistration, DoctorRegistrationAdmin)
docconnect_admin.register(DoctorQualification, DoctorQualificationAdmin)
docconnect_admin.register(DoctorExperience, DoctorExperienceAdmin)
