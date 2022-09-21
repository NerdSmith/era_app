# Generated by Django 3.2.9 on 2021-12-09 10:10

import api.models
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_alter_photoseries_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_pic',
            field=models.ImageField(blank=True, default='site/default.jpg', null=True, upload_to=api.models.User.get_image_path, validators=[django.core.validators.FileExtensionValidator(['png', 'jpg', 'gif'])]),
        ),
    ]