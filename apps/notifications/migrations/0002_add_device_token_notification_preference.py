import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token', models.TextField(unique=True)),
                ('platform', models.CharField(choices=[('ANDROID', 'Android'), ('IOS', 'iOS'), ('WEB', 'Web')], default='ANDROID', max_length=10)),
                ('device_id', models.CharField(blank=True, max_length=255, null=True)),
                ('device_name', models.CharField(blank=True, max_length=255, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='device_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'device_tokens'},
        ),
        migrations.AddIndex(
            model_name='devicetoken',
            index=models.Index(fields=['user', 'is_active'], name='device_tokens_user_active_idx'),
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('connection_request_push', models.BooleanField(default=True)),
                ('connection_request_inapp', models.BooleanField(default=True)),
                ('post_interaction_push', models.BooleanField(default=True)),
                ('post_interaction_inapp', models.BooleanField(default=True)),
                ('new_message_push', models.BooleanField(default=True)),
                ('new_message_inapp', models.BooleanField(default=True)),
                ('job_recommendation_push', models.BooleanField(default=True)),
                ('job_recommendation_inapp', models.BooleanField(default=True)),
                ('application_update_push', models.BooleanField(default=True)),
                ('application_update_inapp', models.BooleanField(default=True)),
                ('shift_request_push', models.BooleanField(default=True)),
                ('shift_request_inapp', models.BooleanField(default=True)),
                ('verification_update_push', models.BooleanField(default=True)),
                ('verification_update_inapp', models.BooleanField(default=True)),
                ('extra', models.JSONField(blank=True, default=dict)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'notification_preferences'},
        ),
    ]
