from __future__ import annotations

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Tag(models.Model):
    tag = models.CharField(max_length=20, blank=False, null=False)

    def __str__(self):
        return self.tag


class SinglePhoto(models.Model):
    photo = models.ImageField(null=False, blank=False, upload_to='pictures/photos')
    owner = models.ForeignKey("UserProfile", on_delete=models.CASCADE, related_name='user_photos', blank=False, null=False)
    series = models.ForeignKey("PhotoSeries", on_delete=models.CASCADE, related_name='series_photos', blank=False, null=False)

    def __str__(self):
        return self.photo.name

    def is_secret(self):
        return self.series.is_secret()


class PhotoSeries(models.Model):
    name = models.CharField(max_length=40, blank=False, null=False)
    tag = models.ManyToManyField(Tag, blank=True, symmetrical=False, related_name='photo_series')
    description = models.TextField(max_length=150, blank=True, null=False)
    owner = models.ForeignKey("UserProfile", on_delete=models.CASCADE, related_name='user_series')
    collection = models.ForeignKey("Collection", on_delete=models.CASCADE, related_name='collection_series', blank=True, null=True)

    def __str__(self):
        return self.name

    def is_secret(self):
        if self.collection:
            return self.collection.is_secret
        else:
            return False


class Collection(models.Model):
    cover = models.ImageField(null=False, blank=False, upload_to='pictures/covers')
    name = models.CharField(max_length=40, blank=False, null=False)
    description = models.TextField(max_length=150, blank=True, null=False)
    is_secret = models.BooleanField(default=False)
    owner = models.ForeignKey("UserProfile", on_delete=models.CASCADE, related_name='user_collections')

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscribers = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='subscribed_to')
    profile_pic = models.ImageField(null=True, blank=True, upload_to='pictures/avatars')
    description = models.TextField(max_length=150, blank=True, null=False)
    location = models.CharField(max_length=50, blank=True, null=False)
    # interests
    instagram_url = models.URLField(blank=True, null=False)
    vk_url = models.URLField(blank=True, null=False)
    SEX_CHOICES = [
        ('m', "male"),
        ('f', "female"),
        ('o', 'other')
    ]
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, default='o')
    # collections

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_custom_user(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_custom_user(sender, instance, **kwargs):
    instance.userprofile.save()


@receiver(models.signals.pre_save, sender=UserProfile)
def delete_file_on_change_extension(sender, instance, ** kwargs):
    if instance.pk:
        try:
            old_avatar = UserProfile.objects.get(pk=instance.pk).profile_pic
        except Exception as e:
            return
        new_avatar = instance.profile_pic
        if new_avatar:
            if old_avatar and old_avatar.url != new_avatar.url:
                old_avatar.delete(save=False)
        else:
            old_avatar.delete(save=False)

