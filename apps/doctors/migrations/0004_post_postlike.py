from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0003_photo_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('post_type', models.CharField(choices=[('UPDATE', 'Update'), ('CASE', 'Clinical Case'), ('ARTICLE', 'Article'), ('PHOTO', 'Photo')], default='UPDATE', max_length=20)),
                ('content', models.TextField()),
                ('image_base64', models.TextField(blank=True, null=True)),
                ('is_anonymous', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='doctors.doctorprofile')),
            ],
            options={'db_table': 'doctor_posts', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='PostLike',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='doctors.post')),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='liked_posts', to='doctors.doctorprofile')),
            ],
            options={'db_table': 'post_likes', 'unique_together': {('post', 'doctor')}},
        ),
    ]
