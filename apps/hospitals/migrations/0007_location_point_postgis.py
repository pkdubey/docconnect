from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Phase 3: Alters location_point on hospitals from JSONField to PostGIS PointField.
    Only runs the ALTER when USE_POSTGIS=true; otherwise remains a no-op JSONField.
    Requires: pip install django[gis], PostgreSQL PostGIS extension, USE_POSTGIS=true in .env.
    """

    dependencies = [
        ('hospitals', '0006_add_location_point'),
    ]

    operations = []

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
                model_name='hospital',
                name='location_point',
                field=PointField(blank=True, geography=True, null=True, srid=4326),
            ),
        ]


try:
    Migration.operations = Migration._get_operations()
except Exception:
    pass
