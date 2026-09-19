import uuid
from django.db import models


class Specialization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'specializations'
        ordering = ['name']

    def __str__(self):
        return self.name


class Qualification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'qualifications'
        ordering = ['name']

    def __str__(self):
        return self.name


class Council(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    short = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'councils'
        ordering = ['name']

    def __str__(self):
        return self.short


class Community(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    specialty_id = models.UUIDField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'communities'
        ordering = ['name']

    @property
    def member_count(self):
        return self.members.count()

    def __str__(self):
        return self.name


class CommunityMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='community_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'community_members'
        unique_together = ('community', 'user')

    def __str__(self):
        return f"{self.user} in {self.community}"


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=50, null=True, blank=True)
    target_id = models.UUIDField(null=True, blank=True)
    performed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} by {self.performed_by}"


class Report(models.Model):
    TARGET_TYPES = [
        ('PROFILE', 'Profile'), ('POST', 'Post'), ('COMMENT', 'Comment'),
        ('JOB', 'Job'), ('HOSPITAL', 'Hospital'),
    ]
    REASON_CODES = [
        ('PATIENT_PRIVACY_CONCERN', 'Patient Privacy Concern'),
        ('POTENTIAL_MEDICAL_MISINFORMATION', 'Potential Medical Misinformation'),
        ('SPAM', 'Spam'),
        ('HARASSMENT', 'Harassment'),
        ('COPYRIGHT_CONCERN', 'Copyright Concern'),
        ('FAKE_DOCTOR_FALSE_CREDENTIALS', 'Fake Doctor / False Credentials'),
        ('PROFESSIONAL_MISCONDUCT_CONCERN', 'Professional Misconduct Concern'),
        ('OTHER_POLICY_VIOLATION', 'Other Policy Violation'),
    ]
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('ACTIONED', 'Actioned'),
        ('DISMISSED', 'Dismissed'),
        ('ESCALATED', 'Escalated'),
    ]
    SEVERITY_CHOICES = [
        ('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='reports_filed')
    target_type = models.CharField(max_length=20, choices=TARGET_TYPES)
    target_id = models.UUIDField()
    reason = models.CharField(max_length=50, choices=REASON_CODES)
    description = models.TextField(null=True, blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    reviewed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_reviewed'
    )
    resolution_notes = models.TextField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status']), models.Index(fields=['target_type', 'target_id'])]

    def __str__(self):
        return f"Report({self.target_type}:{self.target_id}) by {self.reporter_id}"


class ReportEvidence(models.Model):
    """Evidence files attached to a report. Access via signed URLs only — never public."""
    EVIDENCE_TYPES = [
        ('SCREENSHOT', 'Screenshot'),
        ('DOCUMENT', 'Document'),
        ('OTHER', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='evidence')
    evidence_file_id = models.UUIDField()  # references file in private S3 storage
    evidence_type = models.CharField(max_length=20, choices=EVIDENCE_TYPES, default='SCREENSHOT')
    uploaded_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'report_evidence'
        ordering = ['created_at']

    def __str__(self):
        return f"Evidence({self.evidence_type}) for Report({self.report_id})"


class SupportTicket(models.Model):
    CATEGORY_CHOICES = [
        ('GENERAL', 'General'), ('VERIFICATION', 'Verification'),
        ('BILLING', 'Billing'), ('TECHNICAL', 'Technical'),
    ]
    STATUS_CHOICES = [
        ('OPEN', 'Open'), ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'), ('CLOSED', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='GENERAL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    assigned_to = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'support_tickets'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'status']), models.Index(fields=['status'])]

    def __str__(self):
        return f"Ticket({self.subject[:40]}) — {self.status}"


class SupportMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    message = models.TextField()
    is_internal = models.BooleanField(default=False)  # admin-only internal notes
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'support_messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Msg on Ticket({self.ticket_id}) by {self.sender_id}"


class MatchingConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.CharField(max_length=20, unique=True)  # e.g. "v1", "v2"
    is_active = models.BooleanField(default=False)
    weights = models.JSONField(default=dict)  # {"specialization_match": 0.3, ...}
    description = models.TextField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matching_configs'
        ordering = ['-created_at']

    def __str__(self):
        return f"MatchingConfig {self.version} (active={self.is_active})"


class Plan(models.Model):
    """Billing plan definitions."""
    BILLING_CYCLE = [
        ('MONTHLY', 'Monthly'),
        ('ANNUAL', 'Annual'),
        ('ONE_TIME', 'One Time'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLE, default='MONTHLY')
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=list)  # list of feature strings
    limits = models.JSONField(default=dict)    # {"job_posts": 10, "users": 5}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plans'
        ordering = ['price']

    def __str__(self):
        return f"{self.name} ({self.currency} {self.price}/{self.billing_cycle})"


class Subscription(models.Model):
    """Hospital subscription to a billing plan."""
    STATUS = [
        ('ACTIVE', 'Active'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
        ('PAST_DUE', 'Past Due'),
        ('TRIALING', 'Trialing'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey('hospitals.Hospital', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS, default='ACTIVE')
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    provider_subscription_id = models.CharField(max_length=255, null=True, blank=True)  # Razorpay/Stripe ID
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'
        indexes = [models.Index(fields=['hospital', 'status'])]

    def __str__(self):
        return f"{self.hospital.name} — {self.plan.name} ({self.status})"


class Entitlement(models.Model):
    """Active feature entitlements derived from a subscription."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='entitlements')
    feature_key = models.CharField(max_length=100)  # e.g. "job_posts", "candidate_search"
    limit_value = models.IntegerField(null=True, blank=True)  # None = unlimited
    used_value = models.IntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'entitlements'
        unique_together = ('subscription', 'feature_key')

    def __str__(self):
        return f"{self.feature_key} (sub={self.subscription_id})"


class Invoice(models.Model):
    """Billing invoices for subscriptions."""
    STATUS = [
        ('DRAFT', 'Draft'),
        ('OPEN', 'Open'),
        ('PAID', 'Paid'),
        ('VOID', 'Void'),
        ('UNCOLLECTIBLE', 'Uncollectible'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS, default='OPEN')
    due_date = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    provider_invoice_id = models.CharField(max_length=255, null=True, blank=True)
    pdf_url = models.URLField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invoices'
        indexes = [models.Index(fields=['subscription', 'status'])]

    def __str__(self):
        return f"Invoice {self.id} — {self.status} ({self.currency} {self.amount})"


class Payment(models.Model):
    """Individual payment records linked to invoices."""
    STATUS = [
        ('PENDING', 'Pending'),
        ('CAPTURED', 'Captured'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
        ('PARTIALLY_REFUNDED', 'Partially Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=25, choices=STATUS, default='PENDING')
    provider = models.CharField(max_length=50, null=True, blank=True)  # razorpay / stripe
    provider_payment_id = models.CharField(max_length=255, null=True, blank=True)
    refunded_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        indexes = [models.Index(fields=['invoice', 'status'])]

    def __str__(self):
        return f"Payment {self.provider_payment_id} — {self.status}"
