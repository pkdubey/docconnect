from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('hospitals', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HospitalFollow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers', to='hospitals.hospital')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hospital_follows', to='accounts.user')),
            ],
            options={'db_table': 'hospital_follows', 'unique_together': {('user', 'hospital')}},
        ),
    ]
