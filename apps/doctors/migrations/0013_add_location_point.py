from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adds optional location_point field to doctor_profiles.
    When USE_POSTGIS=true, this becomes a PostGIS PointField (srid=4326).
    When USE_POSTGIS=false (default), stored as JSONB null — no PostGIS extension required.
    Existing JSONB professional_location data is preserved; Haversine search continues to work.
    """

    dependencies = [
        ('doctors', '0012_remove_block_unique_block_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorprofile',
            name='location_point',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
