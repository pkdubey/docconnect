from django.contrib import messages
from django.contrib.admin import ModelAdmin, TabularInline, action
from django.utils import timezone
from apps.core.admin_site import docconnect_admin
from .models import (
    DoctorProfile, DoctorRegistration, DoctorQualification, DoctorExperience,
    DoctorAffiliation, Post, PostLike, PostComment, Connection, Follow, Block,
)


# ── Inlines ───────────────────────────────────────────────────

class DoctorRegistrationInline(TabularInline):
    model = DoctorRegistration
    fields = ('registration_number', 'registration_year', 'verification_status', 'verified_at')
    readonly_fields = ('verified_at',)
    extra = 0


class DoctorQualificationInline(TabularInline):
    model = DoctorQualification
    fields = ('degree', 'institution', 'year', 'specialization')
    extra = 0


class DoctorExperienceInline(TabularInline):
    model = DoctorExperience
    fields = ('role', 'hospital_name', 'start_date', 'end_date', 'is_current')
    extra = 0


class DoctorAffiliationInline(TabularInline):
    model = DoctorAffiliation
    fields = ('hospital_name', 'role', 'start_date', 'end_date', 'is_current')
    extra = 0


# ── Doctor Verification Actions (README §5.2) ─────────────────

@action(description='✅ Approve verification (VERIFIED)')
def approve_verification(modeladmin, request, queryset):
    from apps.core.models import AuditLog
    qs = queryset.exclude(verification_status='VERIFIED')
    updated = qs.update(verification_status='VERIFIED', verification_rejected_reason=None)
    for obj in qs:
        AuditLog.objects.create(
            action='DOCTOR_VERIFIED',
            target_type='DOCTOR_PROFILE',
            target_id=obj.id,
            performed_by=request.user,
            metadata={'doctor': str(obj)},
        )
    messages.success(request, f'{updated} doctor(s) verified.')


@action(description='❌ Reject verification (REJECTED)')
def reject_verification(modeladmin, request, queryset):
    from apps.core.models import AuditLog
    qs = queryset.exclude(verification_status='REJECTED')
    updated = qs.update(verification_status='REJECTED')
    for obj in qs:
        AuditLog.objects.create(
            action='DOCTOR_VERIFICATION_REJECTED',
            target_type='DOCTOR_PROFILE',
            target_id=obj.id,
            performed_by=request.user,
            metadata={'doctor': str(obj)},
        )
    messages.warning(request, f'{updated} doctor(s) rejected. Set rejection reason individually.')


@action(description='🔄 Reset to PENDING (allow resubmission)')
def reset_to_pending(modeladmin, request, queryset):
    updated = queryset.update(verification_status='PENDING')
    messages.info(request, f'{updated} doctor(s) reset to PENDING.')


# ── Post Moderation Actions (README §5.1) ─────────────────────

@action(description='🚩 Flag post for PII')
def flag_pii(modeladmin, request, queryset):
    updated = queryset.update(pii_flagged=True)
    messages.warning(request, f'{updated} post(s) flagged for PII.')


@action(description='✅ Clear PII flag')
def clear_pii_flag(modeladmin, request, queryset):
    updated = queryset.update(pii_flagged=False)
    messages.success(request, f'{updated} post(s) PII flag cleared.')


# ── Admins ────────────────────────────────────────────────────

class DoctorProfileAdmin(ModelAdmin):
    list_display = ('full_name', 'user', 'verification_status', 'experience_years', 'open_to_opportunities', 'profile_visibility', 'created_at')
    list_filter = ('verification_status', 'profile_visibility', 'career_visibility', 'open_to_opportunities')
    search_fields = ('first_name', 'last_name', 'user__phone')
    ordering = ('-created_at',)
    exclude = ('metadata', 'search_vector', 'photo_base64', 'cover_base64')
    actions = [approve_verification, reject_verification, reset_to_pending]
    inlines = [DoctorRegistrationInline, DoctorQualificationInline, DoctorExperienceInline, DoctorAffiliationInline]
    fieldsets = (
        ('Identity', {'fields': ('user', 'first_name', 'last_name', 'headline', 'about')}),
        ('Professional', {'fields': ('primary_specialization_id', 'experience_years', 'professional_location', 'languages')}),
        ('Verification', {'fields': ('verification_status', 'verification_rejected_reason')}),
        ('Visibility', {'fields': ('profile_visibility', 'career_visibility', 'open_to_opportunities')}),
    )


class DoctorRegistrationAdmin(ModelAdmin):
    list_display = ('doctor', 'registration_number', 'registration_year', 'verification_status', 'verified_at', 'verified_by')
    list_filter = ('verification_status',)
    search_fields = ('registration_number', 'doctor__first_name', 'doctor__last_name')
    readonly_fields = ('verified_at',)

    @action(description='✅ Mark registration VERIFIED')
    def verify_registration(self, request, queryset):
        updated = queryset.exclude(verification_status='VERIFIED').update(
            verification_status='VERIFIED', verified_at=timezone.now(), verified_by=request.user
        )
        messages.success(request, f'{updated} registration(s) verified.')

    @action(description='❌ Mark registration REJECTED')
    def reject_registration(self, request, queryset):
        updated = queryset.exclude(verification_status='REJECTED').update(verification_status='REJECTED')
        messages.warning(request, f'{updated} registration(s) rejected.')

    actions = ['verify_registration', 'reject_registration']


class DoctorQualificationAdmin(ModelAdmin):
    list_display = ('doctor', 'degree', 'institution', 'year', 'specialization')
    search_fields = ('doctor__first_name', 'degree', 'institution')


class DoctorExperienceAdmin(ModelAdmin):
    list_display = ('doctor', 'role', 'hospital_name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('doctor__first_name', 'hospital_name')


class DoctorAffiliationAdmin(ModelAdmin):
    list_display = ('doctor', 'hospital_name', 'role', 'is_current', 'start_date')
    list_filter = ('is_current',)
    search_fields = ('doctor__first_name', 'hospital_name')


class PostCommentInline(TabularInline):
    model = PostComment
    fields = ('author', 'content', 'parent', 'created_at')
    readonly_fields = ('created_at',)
    extra = 0


@action(description='🗑️ Delete selected posts (moderation)')
def delete_posts(modeladmin, request, queryset):
    from apps.core.models import AuditLog
    for obj in queryset:
        AuditLog.objects.create(
            action='POST_REMOVED_BY_ADMIN',
            target_type='POST',
            target_id=obj.id,
            performed_by=request.user,
            metadata={'post_type': obj.post_type, 'author': str(obj.author)},
        )
    count = queryset.count()
    queryset.delete()
    messages.error(request, f'{count} post(s) removed by admin.')


class PostAdmin(ModelAdmin):
    list_display = ('author', 'post_type', 'is_anonymous', 'patient_privacy_confirmed', 'pii_flagged', 'created_at')
    list_filter = ('post_type', 'is_anonymous', 'pii_flagged', 'patient_privacy_confirmed')
    search_fields = ('author__first_name', 'content')
    ordering = ('-created_at',)
    actions = [flag_pii, clear_pii_flag, delete_posts]
    inlines = [PostCommentInline]
    readonly_fields = ('created_at', 'updated_at')


class PostLikeAdmin(ModelAdmin):
    list_display = ('post', 'liked_by', 'created_at')
    search_fields = ('liked_by__phone',)
    ordering = ('-created_at',)


class PostCommentAdmin(ModelAdmin):
    list_display = ('author', 'post', 'parent', 'created_at')
    search_fields = ('author__phone', 'content')
    ordering = ('-created_at',)


class ConnectionAdmin(ModelAdmin):
    list_display = ('sender', 'receiver', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('sender__first_name', 'receiver__first_name')
    ordering = ('-created_at',)


class FollowAdmin(ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    search_fields = ('follower__phone', 'following__phone')
    ordering = ('-created_at',)


class BlockAdmin(ModelAdmin):
    list_display = ('blocker', 'blocked', 'created_at')
    search_fields = ('blocker__phone', 'blocked__phone')
    ordering = ('-created_at',)


docconnect_admin.register(DoctorProfile, DoctorProfileAdmin)
docconnect_admin.register(DoctorRegistration, DoctorRegistrationAdmin)
docconnect_admin.register(DoctorQualification, DoctorQualificationAdmin)
docconnect_admin.register(DoctorExperience, DoctorExperienceAdmin)
docconnect_admin.register(DoctorAffiliation, DoctorAffiliationAdmin)
docconnect_admin.register(Post, PostAdmin)
docconnect_admin.register(PostComment, PostCommentAdmin)
docconnect_admin.register(PostLike, PostLikeAdmin)
docconnect_admin.register(Connection, ConnectionAdmin)
docconnect_admin.register(Follow, FollowAdmin)
docconnect_admin.register(Block, BlockAdmin)
