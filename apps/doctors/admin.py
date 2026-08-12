from django.contrib.admin import ModelAdmin
from apps.core.admin_site import docconnect_admin
from .models import DoctorProfile, DoctorRegistration, DoctorQualification, DoctorExperience, Post, PostLike


class DoctorProfileAdmin(ModelAdmin):
    list_display = ('full_name', 'user', 'verification_status', 'experience_years', 'created_at')
    list_filter = ('verification_status', 'profile_visibility')
    search_fields = ('first_name', 'last_name', 'user__phone')
    ordering = ('-created_at',)
    exclude = ('metadata', 'search_vector')


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


class PostAdmin(ModelAdmin):
    list_display = ('author', 'post_type', 'is_anonymous', 'created_at')
    list_filter = ('post_type', 'is_anonymous')
    search_fields = ('author__first_name', 'content')
    ordering = ('-created_at',)


docconnect_admin.register(DoctorProfile, DoctorProfileAdmin)
docconnect_admin.register(DoctorRegistration, DoctorRegistrationAdmin)
docconnect_admin.register(DoctorQualification, DoctorQualificationAdmin)
docconnect_admin.register(DoctorExperience, DoctorExperienceAdmin)
docconnect_admin.register(Post, PostAdmin)
