from django.contrib.admin import ModelAdmin
from apps.core.admin_site import docconnect_admin
from .models import DoctorAvailability, AvailabilitySlot


class DoctorAvailabilityAdmin(ModelAdmin):
    list_display = ('doctor', 'availability_type', 'available_from', 'available_until', 'is_active')
    list_filter = ('availability_type', 'is_active')
    search_fields = ('doctor__first_name', 'doctor__last_name')


class AvailabilitySlotAdmin(ModelAdmin):
    list_display = ('availability', 'slot_date', 'start_time', 'end_time', 'is_booked')
    list_filter = ('is_booked',)


docconnect_admin.register(DoctorAvailability, DoctorAvailabilityAdmin)
docconnect_admin.register(AvailabilitySlot, AvailabilitySlotAdmin)
