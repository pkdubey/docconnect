from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_user_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='totp_secret',
            field=models.CharField(max_length=64, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='mfa_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
