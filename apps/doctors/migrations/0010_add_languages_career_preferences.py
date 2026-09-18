from django.db import migrations, models
from django.contrib.postgres.fields import ArrayField


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0009_add_post_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorprofile',
            name='languages',
            field=models.JSONField(default=list, blank=True),
        ),
        migrations.AddField(
            model_name='doctorprofile',
            name='career_preferences',
            field=models.JSONField(default=dict, blank=True),
        ),
        migrations.AddField(
            model_name='post',
            name='patient_privacy_confirmed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='post',
            name='pii_flagged',
            field=models.BooleanField(default=False),
        ),
    ]
