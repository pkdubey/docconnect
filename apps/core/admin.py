from django.contrib import messages
from django.contrib.admin import ModelAdmin, TabularInline, action
from django.utils import timezone
from apps.core.admin_site import docconnect_admin
from .models import (
    Specialization, Qualification, Council,
    Community, CommunityMember,
    AuditLog, Report, ReportEvidence,
    SupportTicket, SupportMessage,
    MatchingConfig,
    Plan, Subscription, Entitlement, Invoice, Payment,
    CMEEvent, CMECredit,
    Endorsement, SecondOpinionRequest, TelemedicineSession,
    HospitalAnalyticsSnapshot,
)


# ── Masters ───────────────────────────────────────────────────

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


# ── Communities ───────────────────────────────────────────────

class CommunityMemberInline(TabularInline):
    model = CommunityMember
    fields = ('user', 'is_moderator', 'joined_at')
    readonly_fields = ('joined_at',)
    extra = 0


class CommunityAdmin(ModelAdmin):
    list_display = ('name', 'member_count', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    inlines = [CommunityMemberInline]

    @action(description='📦 Archive selected communities')
    def archive_communities(self, request, queryset):
        from apps.core.models import AuditLog
        updated = queryset.filter(is_active=True).update(is_active=False)
        for obj in queryset:
            AuditLog.objects.create(
                action='COMMUNITY_ARCHIVED',
                target_type='COMMUNITY',
                target_id=obj.id,
                performed_by=request.user,
                metadata={'name': obj.name},
            )
        messages.warning(request, f'{updated} community/communities archived.')

    @action(description='✅ Restore (unarchive) selected communities')
    def restore_communities(self, request, queryset):
        updated = queryset.filter(is_active=False).update(is_active=True)
        messages.success(request, f'{updated} community/communities restored.')

    actions = ['archive_communities', 'restore_communities']


class CommunityMemberAdmin(ModelAdmin):
    list_display = ('community', 'user', 'is_moderator', 'joined_at')
    list_filter = ('is_moderator',)
    search_fields = ('user__phone', 'community__name')


# ── Audit Log ─────────────────────────────────────────────────

class AuditLogAdmin(ModelAdmin):
    list_display = ('action', 'target_type', 'target_id', 'performed_by', 'created_at')
    list_filter = ('action', 'target_type')
    search_fields = ('action', 'performed_by__phone')
    readonly_fields = ('id', 'action', 'target_type', 'target_id', 'performed_by', 'metadata', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ── Report Actions (README §5.3 lifecycle) ───────────────────

@action(description='🔍 Mark as Under Review')
def mark_under_review(modeladmin, request, queryset):
    updated = queryset.filter(status='SUBMITTED').update(status='UNDER_REVIEW')
    messages.info(request, f'{updated} report(s) marked Under Review.')


@action(description='✅ Action selected reports')
def action_reports(modeladmin, request, queryset):
    updated = queryset.filter(status__in=['SUBMITTED', 'UNDER_REVIEW']).update(
        status='ACTIONED', reviewed_by=request.user, resolved_at=timezone.now()
    )
    messages.success(request, f'{updated} report(s) actioned.')


@action(description='🚫 Dismiss selected reports')
def dismiss_reports(modeladmin, request, queryset):
    updated = queryset.filter(status__in=['SUBMITTED', 'UNDER_REVIEW']).update(
        status='DISMISSED', reviewed_by=request.user, resolved_at=timezone.now()
    )
    messages.warning(request, f'{updated} report(s) dismissed.')


@action(description='⬆️ Escalate selected reports')
def escalate_reports(modeladmin, request, queryset):
    updated = queryset.filter(status__in=['SUBMITTED', 'UNDER_REVIEW']).update(
        status='ESCALATED', reviewed_by=request.user
    )
    messages.error(request, f'{updated} report(s) escalated.')


# ── Reports ───────────────────────────────────────────────────

class ReportEvidenceInline(TabularInline):
    model = ReportEvidence
    fields = ('evidence_type', 'evidence_file_id', 'uploaded_by', 'created_at')
    readonly_fields = ('created_at',)
    extra = 0


class ReportAdmin(ModelAdmin):
    list_display = ('id', 'target_type', 'reason', 'severity', 'status', 'reporter', 'reviewed_by', 'created_at')
    list_filter = ('status', 'severity', 'target_type', 'reason')
    search_fields = ('reporter__phone',)
    readonly_fields = ('id', 'reporter', 'target_type', 'target_id', 'created_at')
    ordering = ('-created_at',)
    actions = [mark_under_review, action_reports, dismiss_reports, escalate_reports]
    inlines = [ReportEvidenceInline]
    fieldsets = (
        ('Report Info', {'fields': ('id', 'reporter', 'target_type', 'target_id', 'reason', 'description', 'severity')}),
        ('Resolution', {'fields': ('status', 'reviewed_by', 'resolution_notes', 'resolved_at')}),
    )


# ── Support ───────────────────────────────────────────────────

class SupportMessageInline(TabularInline):
    model = SupportMessage
    fields = ('sender', 'message', 'is_internal', 'created_at')
    readonly_fields = ('created_at',)
    extra = 1


@action(description='📋 Assign to me')
def assign_to_me(modeladmin, request, queryset):
    updated = queryset.filter(status='OPEN').update(
        assigned_to=request.user, status='IN_PROGRESS'
    )
    messages.success(request, f'{updated} ticket(s) assigned to you.')


@action(description='✅ Mark as Resolved')
def resolve_tickets(modeladmin, request, queryset):
    updated = queryset.exclude(status__in=['RESOLVED', 'CLOSED']).update(
        status='RESOLVED', resolved_at=timezone.now()
    )
    messages.success(request, f'{updated} ticket(s) resolved.')


@action(description='🔒 Close tickets')
def close_tickets(modeladmin, request, queryset):
    updated = queryset.exclude(status='CLOSED').update(status='CLOSED')
    messages.info(request, f'{updated} ticket(s) closed.')


class SupportTicketAdmin(ModelAdmin):
    list_display = ('subject', 'user', 'category', 'status', 'assigned_to', 'created_at', 'resolved_at')
    list_filter = ('status', 'category')
    search_fields = ('subject', 'user__phone')
    ordering = ('-created_at',)
    actions = [assign_to_me, resolve_tickets, close_tickets]
    inlines = [SupportMessageInline]
    fieldsets = (
        ('Ticket', {'fields': ('user', 'subject', 'description', 'category')}),
        ('Status', {'fields': ('status', 'assigned_to', 'resolved_at')}),
    )


class SupportMessageAdmin(ModelAdmin):
    list_display = ('ticket', 'sender', 'is_internal', 'created_at')
    list_filter = ('is_internal',)
    search_fields = ('sender__phone', 'message', 'ticket__subject')
    ordering = ('-created_at',)

    def has_change_permission(self, request, obj=None):
        return False


class EntitlementAdmin(ModelAdmin):
    list_display = ('subscription', 'feature_key', 'limit_value', 'used_value', 'expires_at')
    list_filter = ('feature_key',)
    search_fields = ('subscription__hospital__name', 'feature_key')
    ordering = ('-created_at',)


# ── Matching Config ───────────────────────────────────────────

class MatchingConfigAdmin(ModelAdmin):
    list_display = ('version', 'is_active', 'approved_by', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('version',)
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        # Activating a config deactivates all others atomically
        if obj.is_active:
            MatchingConfig.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)


# ── Billing ───────────────────────────────────────────────────

class EntitlementInline(TabularInline):
    model = Entitlement
    fields = ('feature_key', 'limit_value', 'used_value', 'expires_at')
    extra = 0


class InvoiceInline(TabularInline):
    model = Invoice
    fields = ('amount', 'currency', 'status', 'due_date', 'paid_at')
    readonly_fields = ('created_at',)
    extra = 0


class PlanAdmin(ModelAdmin):
    list_display = ('name', 'price', 'currency', 'billing_cycle', 'is_active')
    list_filter = ('billing_cycle', 'is_active')
    search_fields = ('name',)


class SubscriptionAdmin(ModelAdmin):
    list_display = ('hospital', 'plan', 'status', 'started_at', 'expires_at')
    list_filter = ('status',)
    search_fields = ('hospital__name',)
    inlines = [EntitlementInline, InvoiceInline]


class InvoiceAdmin(ModelAdmin):
    list_display = ('id', 'subscription', 'amount', 'currency', 'status', 'due_date', 'paid_at')
    list_filter = ('status', 'currency')
    search_fields = ('subscription__hospital__name',)
    ordering = ('-created_at',)


class PaymentAdmin(ModelAdmin):
    list_display = ('provider_payment_id', 'invoice', 'amount', 'status', 'provider', 'created_at')
    list_filter = ('status', 'provider')
    search_fields = ('provider_payment_id',)
    ordering = ('-created_at',)


# ── CME ───────────────────────────────────────────────────────

class CMEEventAdmin(ModelAdmin):
    list_display = ('title', 'provider', 'credit_hours', 'event_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'provider')
    ordering = ('-event_date',)


@action(description='✅ Verify CME credits')
def verify_cme_credits(modeladmin, request, queryset):
    updated = queryset.exclude(status='VERIFIED').update(status='VERIFIED')
    messages.success(request, f'{updated} CME credit(s) verified.')


@action(description='❌ Reject CME credits')
def reject_cme_credits(modeladmin, request, queryset):
    updated = queryset.exclude(status='REJECTED').update(status='REJECTED')
    messages.warning(request, f'{updated} CME credit(s) rejected.')


class CMECreditAdmin(ModelAdmin):
    list_display = ('doctor', 'title', 'credits', 'completion_date', 'status')
    list_filter = ('status',)
    search_fields = ('doctor__first_name', 'doctor__last_name', 'title')
    ordering = ('-completion_date',)
    actions = [verify_cme_credits, reject_cme_credits]


# ── Phase 3 ───────────────────────────────────────────────────

class EndorsementAdmin(ModelAdmin):
    list_display = ('endorser', 'endorsed', 'skill', 'created_at')
    search_fields = ('skill', 'endorser__phone', 'endorsed__first_name')
    ordering = ('-created_at',)


class SecondOpinionRequestAdmin(ModelAdmin):
    list_display = ('requester', 'reviewer', 'status', 'is_anonymous', 'created_at')
    list_filter = ('status', 'is_anonymous')
    search_fields = ('requester__first_name', 'reviewer__first_name')
    ordering = ('-created_at',)


class TelemedicineSessionAdmin(ModelAdmin):
    list_display = ('host', 'guest_doctor', 'session_type', 'status', 'scheduled_at', 'duration_minutes')
    list_filter = ('session_type', 'status')
    search_fields = ('host__first_name',)
    ordering = ('-scheduled_at',)


class HospitalAnalyticsSnapshotAdmin(ModelAdmin):
    list_display = ('hospital', 'snapshot_date', 'total_jobs_active', 'total_applications', 'total_hired', 'total_shifts_filled')
    list_filter = ('snapshot_date',)
    search_fields = ('hospital__name',)
    ordering = ('-snapshot_date',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ── Register All ─────────────────────────────────────────────

docconnect_admin.register(Specialization, SpecializationAdmin)
docconnect_admin.register(Qualification, QualificationAdmin)
docconnect_admin.register(Council, CouncilAdmin)
docconnect_admin.register(Community, CommunityAdmin)
docconnect_admin.register(CommunityMember, CommunityMemberAdmin)
docconnect_admin.register(AuditLog, AuditLogAdmin)
docconnect_admin.register(Report, ReportAdmin)
docconnect_admin.register(SupportTicket, SupportTicketAdmin)
docconnect_admin.register(SupportMessage, SupportMessageAdmin)
docconnect_admin.register(MatchingConfig, MatchingConfigAdmin)
docconnect_admin.register(Plan, PlanAdmin)
docconnect_admin.register(Subscription, SubscriptionAdmin)
docconnect_admin.register(Entitlement, EntitlementAdmin)
docconnect_admin.register(Invoice, InvoiceAdmin)
docconnect_admin.register(Payment, PaymentAdmin)
docconnect_admin.register(CMEEvent, CMEEventAdmin)
docconnect_admin.register(CMECredit, CMECreditAdmin)
docconnect_admin.register(Endorsement, EndorsementAdmin)
docconnect_admin.register(SecondOpinionRequest, SecondOpinionRequestAdmin)
docconnect_admin.register(TelemedicineSession, TelemedicineSessionAdmin)
docconnect_admin.register(HospitalAnalyticsSnapshot, HospitalAnalyticsSnapshotAdmin)
