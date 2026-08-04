from django.contrib.admin import ModelAdmin
from apps.core.admin_site import docconnect_admin
from .models import ShiftRequirement, ShiftRequest


class ShiftRequirementAdmin(ModelAdmin):
    list_display = ('hospital', 'requirement_date', 'urgency', 'status', 'doctors_required')
    list_filter = ('urgency', 'status')
    search_fields = ('hospital__name',)


class ShiftRequestAdmin(ModelAdmin):
    list_display = ('doctor', 'requirement', 'status', 'requested_at')
    list_filter = ('status',)
    search_fields = ('doctor__first_name',)


docconnect_admin.register(ShiftRequirement, ShiftRequirementAdmin)
docconnect_admin.register(ShiftRequest, ShiftRequestAdmin)
