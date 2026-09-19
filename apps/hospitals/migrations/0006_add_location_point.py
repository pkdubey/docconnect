from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adds optional location_point field to hospitals.
    When USE_POSTGIS=true, this becomes a PostGIS PointField (srid=4326).
    When USE_POSTGIS=false (default), stored as JSONB null — no PostGIS extension required.
    """

    dependencies = [
        ('hospitals', '0005_add_hospitaluser_permissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospital',
            name='location_point',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
