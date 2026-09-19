from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hospitals', '0004_add_hospital_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospitaluser',
            name='permissions',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
