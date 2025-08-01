# Generated by Django 4.2.10 on 2025-06-15 14:26

from django.db import migrations, models
import paletta_core.storage


class Migration(migrations.Migration):

    dependencies = [
        ('libraries', '0003_remove_library_storage_limit_library_storage_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='library',
            name='logo',
            field=models.ImageField(blank=True, null=True, storage=paletta_core.storage.get_media_storage, upload_to='library_logos/'),
        ),
    ]
