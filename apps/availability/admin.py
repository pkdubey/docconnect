from django.contrib import messages
from django.contrib.admin import ModelAdmin, TabularInline, action
from apps.core.admin_site import docconnect_admin
from .models import DoctorAvailability, AvailabilitySlot


class AvailabilitySlotInline(TabularInline):
    model = AvailabilitySlot
    fields = ('slot_date', 'start_time', 'end_time', 'is_booked')
    extra = 0


@action(description='🔴 Deactivate selected availabilities')
def deactivate_availability(modeladmin, request, queryset):
    updated = queryset.filter(is_active=True).update(is_active=False)
    messages.warning(request, f'{updated} availability record(s) deactivated.')


@action(description='🟢 Activate selected availabilities')
def activate_availability(modeladmin, request, queryset):
    updated = queryset.filter(is_active=False).update(is_active=True)
    messages.success(request, f'{updated} availability record(s) activated.')


class DoctorAvailabilityAdmin(ModelAdmin):
    list_display = ('doctor', 'availability_type', 'available_from', 'available_until', 'minimum_compensation', 'currency', 'is_active')
    list_filter = ('availability_type', 'is_active')
    search_fields = ('doctor__first_name', 'doctor__last_name')
    ordering = ('-created_at',)
    actions = [deactivate_availability, activate_availability]
    inlines = [AvailabilitySlotInline]
    fieldsets = (
        ('Availability', {'fields': ('doctor', 'availability_type', 'available_from', 'available_until', 'is_active')}),
        ('Location & Pay', {'fields': ('preferred_location', 'preferred_radius_km', 'minimum_compensation', 'currency')}),
        ('Notes', {'fields': ('notes',)}),
    )


class AvailabilitySlotAdmin(ModelAdmin):
    list_display = ('availability', 'slot_date', 'start_time', 'end_time', 'is_booked')
    list_filter = ('is_booked', 'slot_date')
    search_fields = ('availability__doctor__first_name',)
    ordering = ('slot_date', 'start_time')


docconnect_admin.register(DoctorAvailability, DoctorAvailabilityAdmin)
docconnect_admin.register(AvailabilitySlot, AvailabilitySlotAdmin)
