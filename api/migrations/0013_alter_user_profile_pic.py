# Generated by Django 3.2.9 on 2021-12-09 10:11

import api.models
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_alter_user_profile_pic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_pic',
            field=models.ImageField(default='site/default.jpg', upload_to=api.models.User.get_image_path, validators=[django.core.validators.FileExtensionValidator(['png', 'jpg', 'gif'])]),
        ),
    ]
