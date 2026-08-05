import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(
                    choices=[('PENDING','Pending'),('ACCEPTED','Accepted'),('DECLINED','Declined'),('WITHDRAWN','Withdrawn')],
                    default='PENDING', max_length=20
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sender', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sent_connections',
                    to='doctors.doctorprofile',
                )),
                ('receiver', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='received_connections',
                    to='doctors.doctorprofile',
                )),
            ],
            options={'db_table': 'doctor_connections', 'unique_together': {('sender', 'receiver')}},
        ),
    ]
