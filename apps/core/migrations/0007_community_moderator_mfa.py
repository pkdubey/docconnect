from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_rename_invoices_subscription_status_idx_invoices_subscri_cd89af_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='communitymember',
            name='is_moderator',
            field=models.BooleanField(default=False),
        ),
    ]
