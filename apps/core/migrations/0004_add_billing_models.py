import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_add_report_supportticket_matchingconfig'),
        ('hospitals', '0004_add_hospital_metadata'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('billing_cycle', models.CharField(choices=[('MONTHLY', 'Monthly'), ('ANNUAL', 'Annual'), ('ONE_TIME', 'One Time')], default='MONTHLY', max_length=10)),
                ('is_active', models.BooleanField(default=True)),
                ('features', models.JSONField(default=list)),
                ('limits', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'plans', 'ordering': ['price']},
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('CANCELLED', 'Cancelled'), ('EXPIRED', 'Expired'), ('PAST_DUE', 'Past Due'), ('TRIALING', 'Trialing')], default='ACTIVE', max_length=20)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('provider_subscription_id', models.CharField(blank=True, max_length=255, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='hospitals.hospital')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subscriptions', to='core.plan')),
            ],
            options={'db_table': 'subscriptions'},
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['hospital', 'status'], name='subscriptions_hospital_status_idx'),
        ),
        migrations.CreateModel(
            name='Entitlement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('feature_key', models.CharField(max_length=100)),
                ('limit_value', models.IntegerField(blank=True, null=True)),
                ('used_value', models.IntegerField(default=0)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entitlements', to='core.subscription')),
            ],
            options={'db_table': 'entitlements'},
        ),
        migrations.AlterUniqueTogether(
            name='entitlement',
            unique_together={('subscription', 'feature_key')},
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('OPEN', 'Open'), ('PAID', 'Paid'), ('VOID', 'Void'), ('UNCOLLECTIBLE', 'Uncollectible')], default='OPEN', max_length=20)),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('provider_invoice_id', models.CharField(blank=True, max_length=255, null=True)),
                ('pdf_url', models.URLField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='core.subscription')),
            ],
            options={'db_table': 'invoices'},
        ),
        migrations.AddIndex(
            model_name='invoice',
            index=models.Index(fields=['subscription', 'status'], name='invoices_subscription_status_idx'),
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('CAPTURED', 'Captured'), ('FAILED', 'Failed'), ('REFUNDED', 'Refunded'), ('PARTIALLY_REFUNDED', 'Partially Refunded')], default='PENDING', max_length=25)),
                ('provider', models.CharField(blank=True, max_length=50, null=True)),
                ('provider_payment_id', models.CharField(blank=True, max_length=255, null=True)),
                ('refunded_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='core.invoice')),
            ],
            options={'db_table': 'payments'},
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['invoice', 'status'], name='payments_invoice_status_idx'),
        ),
    ]
