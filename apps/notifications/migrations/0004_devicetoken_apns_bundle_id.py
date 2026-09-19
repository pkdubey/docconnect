from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_rename_device_tokens_user_active_idx_device_toke_user_id_e99165_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='devicetoken',
            name='bundle_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='devicetoken',
            name='platform',
            field=models.CharField(
                choices=[('FCM', 'FCM (Android/Firebase)'), ('APNS', 'APNs (iOS)'), ('WEB', 'Web')],
                default='FCM',
                max_length=10,
            ),
        ),
    ]
