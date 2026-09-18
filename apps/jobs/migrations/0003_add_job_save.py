import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_add_community_auditlog_application_metadata'),
        ('doctors', '0011_add_affiliation_follow_block'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobSave',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_jobs', to='doctors.doctorprofile')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saves', to='jobs.jobpost')),
            ],
            options={'db_table': 'job_saves'},
        ),
        migrations.AlterUniqueTogether(
            name='jobsave',
            unique_together={('doctor', 'job')},
        ),
    ]
