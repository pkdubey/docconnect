from django.contrib.admin import ModelAdmin
from apps.core.admin_site import docconnect_admin
from .models import Specialization, Qualification, Council


class SpecializationAdmin(ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


class QualificationAdmin(ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


class CouncilAdmin(ModelAdmin):
    list_display = ('name', 'short', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'short')


docconnect_admin.register(Specialization, SpecializationAdmin)
docconnect_admin.register(Qualification, QualificationAdmin)
docconnect_admin.register(Council, CouncilAdmin)
