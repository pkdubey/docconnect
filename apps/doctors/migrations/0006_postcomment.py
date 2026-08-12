from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('doctors', '0005_post_posted_by_author_nullable'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostComment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='doctors.post')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_comments', to='accounts.user')),
            ],
            options={'db_table': 'post_comments', 'ordering': ['created_at']},
        ),
    ]
