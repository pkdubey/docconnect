from django.db import migrations, models


class Migration(migrations.Migration):
    """Phase 3: adds preferred_language (BCP-47 code) to doctor_profiles."""

    dependencies = [
        ('doctors', '0014_location_point_postgis'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorprofile',
            name='preferred_language',
            field=models.CharField(default='en', max_length=10),
        ),
    ]
