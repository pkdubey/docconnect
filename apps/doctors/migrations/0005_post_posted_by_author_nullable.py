from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('doctors', '0004_post_postlike'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='posted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='posts',
                to='accounts.user',
            ),
        ),
        migrations.AlterField(
            model_name='post',
            name='author',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='posts',
                to='doctors.doctorprofile',
            ),
        ),
    ]
