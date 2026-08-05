from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0002_connection'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorprofile',
            name='photo_base64',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='doctorprofile',
            name='cover_base64',
            field=models.TextField(null=True, blank=True),
        ),
    ]
