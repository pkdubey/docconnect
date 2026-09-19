from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Phase 3: Alters location_point on doctor_profiles from JSONField to PostGIS PointField.
    Only runs the ALTER when USE_POSTGIS=true; otherwise remains a no-op JSONField.
    Requires: pip install django[gis], PostgreSQL PostGIS extension, USE_POSTGIS=true in .env.
    Existing JSONB professional_location data is preserved; Haversine fallback still works.
    """

    dependencies = [
        ('doctors', '0013_add_location_point'),
    ]

    operations = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    @classmethod
    def _get_operations(cls):
        if not getattr(settings, 'USE_POSTGIS', False):
            return []
        from django.contrib.gis.db.models import PointField
        return [
            migrations.RunSQL(
                "CREATE EXTENSION IF NOT EXISTS postgis;",
                reverse_sql=migrations.RunSQL.noop,
            ),
            migrations.AlterField(
                model_name='doctorprofile',
                name='location_point',
                field=PointField(blank=True, geography=True, null=True, srid=4326),
            ),
        ]


# Dynamically populate operations at import time (after settings are loaded)
try:
    Migration.operations = Migration._get_operations()
except Exception:
    pass
