import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_community_moderator_mfa'),
        ('doctors', '0014_location_point_postgis'),
        ('hospitals', '0007_location_point_postgis'),
        ('accounts', '0004_add_mfa_fields'),
    ]

    operations = [
        # CMEEvent
        migrations.CreateModel(
            name='CMEEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('provider', models.CharField(max_length=255)),
                ('specialty_id', models.UUIDField(blank=True, null=True)),
                ('credit_hours', models.DecimalField(decimal_places=2, max_digits=6)),
                ('event_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'cme_events', 'ordering': ['-event_date']},
        ),
        # CMECredit
        migrations.CreateModel(
            name='CMECredit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('doctor', models.ForeignKey('doctors.DoctorProfile', on_delete=django.db.models.deletion.CASCADE, related_name='cme_credits')),
                ('event', models.ForeignKey('core.CMEEvent', blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='credits')),
                ('title', models.CharField(max_length=255)),
                ('provider', models.CharField(blank=True, max_length=255, null=True)),
                ('credits', models.DecimalField(decimal_places=2, max_digits=6)),
                ('completion_date', models.DateField()),
                ('certificate_file_id', models.UUIDField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('VERIFIED', 'Verified'), ('REJECTED', 'Rejected')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'cme_credits', 'ordering': ['-completion_date'],
                     'indexes': [models.Index(fields=['doctor', 'status'], name='cme_credits_doctor_status_idx')]},
        ),
        # Endorsement
        migrations.CreateModel(
            name='Endorsement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('endorser', models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE, related_name='endorsements_given')),
                ('endorsed', models.ForeignKey('doctors.DoctorProfile', on_delete=django.db.models.deletion.CASCADE, related_name='endorsements')),
                ('skill', models.CharField(max_length=100)),
                ('note', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'endorsements',
                     'indexes': [models.Index(fields=['endorsed', 'skill'], name='endorsements_endorsed_skill_idx')]},
        ),
        migrations.AddConstraint(
            model_name='endorsement',
            constraint=models.UniqueConstraint(fields=['endorser', 'endorsed', 'skill'], name='unique_endorsement'),
        ),
        # SecondOpinionRequest
        migrations.CreateModel(
            name='SecondOpinionRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('requester', models.ForeignKey('doctors.DoctorProfile', on_delete=django.db.models.deletion.CASCADE, related_name='opinion_requests_sent')),
                ('reviewer', models.ForeignKey('doctors.DoctorProfile', on_delete=django.db.models.deletion.CASCADE, related_name='opinion_requests_received')),
                ('post', models.ForeignKey('doctors.Post', blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='opinion_requests')),
                ('clinical_summary', models.TextField()),
                ('is_anonymous', models.BooleanField(default=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('DECLINED', 'Declined'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=20)),
                ('response', models.TextField(blank=True, null=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'second_opinion_requests', 'ordering': ['-created_at'],
                     'indexes': [models.Index(fields=['reviewer', 'status'], name='opinion_reviewer_status_idx')]},
        ),
        # TelemedicineSession
        migrations.CreateModel(
            name='TelemedicineSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('host', models.ForeignKey('doctors.DoctorProfile', on_delete=django.db.models.deletion.CASCADE, related_name='tele_sessions_hosted')),
                ('guest_doctor', models.ForeignKey('doctors.DoctorProfile', blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tele_sessions_guest')),
                ('session_type', models.CharField(choices=[('CONSULTATION', 'Patient Consultation'), ('PEER_REVIEW', 'Peer Review')], default='CONSULTATION', max_length=20)),
                ('scheduled_at', models.DateTimeField()),
                ('duration_minutes', models.IntegerField(default=30)),
                ('status', models.CharField(choices=[('SCHEDULED', 'Scheduled'), ('IN_PROGRESS', 'In Progress'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled'), ('NO_SHOW', 'No Show')], default='SCHEDULED', max_length=20)),
                ('meeting_link', models.URLField(blank=True, null=True)),
                ('meeting_id', models.CharField(blank=True, max_length=255, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'telemedicine_sessions', 'ordering': ['-scheduled_at'],
                     'indexes': [models.Index(fields=['host', 'status'], name='tele_host_status_idx'),
                                 models.Index(fields=['scheduled_at'], name='tele_scheduled_at_idx')]},
        ),
        # HospitalAnalyticsSnapshot
        migrations.CreateModel(
            name='HospitalAnalyticsSnapshot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('hospital', models.ForeignKey('hospitals.Hospital', on_delete=django.db.models.deletion.CASCADE, related_name='analytics_snapshots')),
                ('snapshot_date', models.DateField()),
                ('total_jobs_active', models.IntegerField(default=0)),
                ('total_applications', models.IntegerField(default=0)),
                ('total_hired', models.IntegerField(default=0)),
                ('total_shifts_filled', models.IntegerField(default=0)),
                ('total_shifts_open', models.IntegerField(default=0)),
                ('avg_time_to_hire_days', models.DecimalField(blank=True, decimal_places=1, max_digits=6, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'hospital_analytics_snapshots', 'ordering': ['-snapshot_date']},
        ),
        migrations.AddConstraint(
            model_name='hospitalanalyticssnapshot',
            constraint=models.UniqueConstraint(fields=['hospital', 'snapshot_date'], name='unique_hospital_snapshot_date'),
        ),
    ]
