from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group, Permission
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


class DocConnectAdminSite(AdminSite):
    site_header = "DocConnect Admin"
    site_title = "DocConnect Admin"
    index_title = "Dashboard"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [path('change-password/', self.admin_view(self.change_password_view), name='change_password')]
        return custom + urls

    def change_password_view(self, request):
        if request.method == 'POST':
            current = request.POST.get('current_password', '')
            new_pw = request.POST.get('new_password', '')
            confirm = request.POST.get('confirm_password', '')
            if not request.user.check_password(current):
                messages.error(request, 'Current password is incorrect.')
            elif new_pw != confirm:
                messages.error(request, 'New passwords do not match.')
            elif len(new_pw) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
            else:
                request.user.set_password(new_pw)
                request.user.save()
                messages.success(request, 'Password changed successfully. Please log in again.')
                return redirect('/admin/login/')
        context = {
            **self.each_context(request),
            'title': 'Change Password',
        }
        return render(request, 'admin/change_password.html', context)

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        try:
            from apps.doctors.models import DoctorProfile
            from apps.hospitals.models import Hospital
            from apps.jobs.models import JobPost, JobApplication
            from apps.availability.models import DoctorAvailability
            from apps.shifts.models import ShiftRequirement
            from apps.messaging.models import Conversation
            from apps.notifications.models import Notification
            from .models import Report, SupportTicket, Community, CMECredit
            extra_context.update({
                'doctors_count':              DoctorProfile.objects.count(),
                'verified_doctors_count':     DoctorProfile.objects.filter(verification_status='VERIFIED').count(),
                'pending_verification':       DoctorProfile.objects.filter(verification_status='PENDING').count(),
                'hospitals_count':            Hospital.objects.count(),
                'verified_hospitals_count':   Hospital.objects.filter(verification_status='VERIFIED').count(),
                'pending_hospital_verification': Hospital.objects.filter(verification_status='PENDING').count(),
                'jobs_count':                 JobPost.objects.filter(status='PUBLISHED').count(),
                'urgent_count':               JobPost.objects.filter(status='PUBLISHED', is_urgent=True).count(),
                'applications_count':         JobApplication.objects.count(),
                'availability_count':         DoctorAvailability.objects.filter(is_active=True).count(),
                'open_shifts_count':          ShiftRequirement.objects.filter(status='OPEN').count(),
                'pending_reports_count':      Report.objects.filter(status='SUBMITTED').count(),
                'escalated_reports_count':    Report.objects.filter(status='ESCALATED').count(),
                'open_tickets_count':         SupportTicket.objects.filter(status__in=['OPEN', 'IN_PROGRESS']).count(),
                'conversations_count':        Conversation.objects.count(),
                'unread_notifications_count': Notification.objects.filter(is_read=False).count(),
                'communities_count':          Community.objects.filter(is_active=True).count(),
                'pending_cme_count':          CMECredit.objects.filter(status='PENDING').count(),
            })
        except Exception:
            extra_context.update({
                'doctors_count': 0, 'verified_doctors_count': 0, 'pending_verification': 0,
                'hospitals_count': 0, 'verified_hospitals_count': 0, 'pending_hospital_verification': 0,
                'jobs_count': 0, 'urgent_count': 0, 'applications_count': 0,
                'availability_count': 0, 'open_shifts_count': 0,
                'pending_reports_count': 0, 'escalated_reports_count': 0,
                'open_tickets_count': 0, 'conversations_count': 0,
                'unread_notifications_count': 0, 'communities_count': 0, 'pending_cme_count': 0,
            })
        return super().index(request, extra_context)


docconnect_admin = DocConnectAdminSite(name='admin')

# Register auth models needed by UserAdmin (groups, permissions)
docconnect_admin.register(Group, GroupAdmin)


class PermissionAdmin(ModelAdmin):
    list_display = ('name', 'codename', 'content_type')
    search_fields = ('name', 'codename')


docconnect_admin.register(Permission, PermissionAdmin)
