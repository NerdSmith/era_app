from __future__ import annotations

from django.contrib.auth.hashers import make_password
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib import auth
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.apps import apps

from .validators import CustomUnicodeUsernameValidator


class Tag(models.Model):
    tag = models.CharField(max_length=20, blank=False, null=False)

    def __str__(self):
        return self.tag


class SinglePhoto(models.Model):
    photo = models.ImageField(null=False, blank=False, upload_to='pictures/photos')
    owner = models.ForeignKey("User", on_delete=models.CASCADE, related_name='user_photos', blank=False, null=False)
    series = models.ForeignKey("PhotoSeries", on_delete=models.CASCADE, related_name='series_photos', blank=False, null=False)
    order = models.IntegerField(null=False, blank=False, default=0)

    def __str__(self):
        return self.photo.name

    def is_secret(self):
        return self.series.is_secret()


class PhotoSeries(models.Model):
    name = models.CharField(max_length=40, blank=False, null=False)
    tag = models.ManyToManyField(Tag, blank=True, symmetrical=False, related_name='photo_series')
    description = models.TextField(max_length=150, blank=True, null=False)
    owner = models.ForeignKey("User", on_delete=models.CASCADE, related_name='user_series')
    collection = models.ManyToManyField("Collection", blank=True, symmetrical=False, related_name='collections_series')
    # collection = models.ForeignKey("Collection", on_delete=models.SET_NULL, related_name='collection_series', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0.0, null=True, blank=True)

    def __str__(self):
        return self.name

    def is_secret(self):
        if self.collection:
            is_secret = False
            for collection in self.collection.all():
                is_secret = is_secret or collection.is_secret

            return is_secret
        else:
            return False


class Collection(models.Model):
    cover = models.ImageField(null=False, blank=False, upload_to='pictures/covers')
    name = models.CharField(max_length=40, blank=False, null=False)
    description = models.TextField(max_length=150, blank=True, null=False)
    is_secret = models.BooleanField(default=False)
    owner = models.ForeignKey("User", on_delete=models.CASCADE, related_name='user_collections')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)

        GlobalUserModel = apps.get_model(self.model._meta.app_label, self.model._meta.object_name)
        username = GlobalUserModel.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)

    def with_perm(self, perm, is_active=True, include_superusers=True, backend=None, obj=None):
        if backend is None:
            backends = auth._get_backends(return_tuples=True)
            if len(backends) == 1:
                backend, _ = backends[0]
            else:
                raise ValueError(
                    'You have multiple authentication backends configured and '
                    'therefore must provide the `backend` argument.'
                )
        elif not isinstance(backend, str):
            raise TypeError(
                'backend must be a dotted import path string (got %r).'
                % backend
            )
        else:
            backend = auth.load_backend(backend)
        if hasattr(backend, 'with_perm'):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()


class User(AbstractBaseUser, PermissionsMixin):
    username_validator = CustomUnicodeUsernameValidator()
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    # profile features
    subscribers = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='subscribed_to')
    profile_pic = models.ImageField(null=True, blank=True, upload_to='pictures/avatars')
    check_mark = models.BooleanField(_('check mark'), default=False, blank=False, null=False)
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

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', ]

    def get_full_name(self):
        return self.first_name

    def get_short_name(self):
        return self.first_name

    def __str__(self):
        return self.username




# class UserProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     subscribers = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='subscribed_to')
#     profile_pic = models.ImageField(null=True, blank=True, upload_to='pictures/avatars')
#     description = models.TextField(max_length=150, blank=True, null=False)
#     location = models.CharField(max_length=50, blank=True, null=False)
#     # interests
#     instagram_url = models.URLField(blank=True, null=False)
#     vk_url = models.URLField(blank=True, null=False)
#     SEX_CHOICES = [
#         ('m', "male"),
#         ('f', "female"),
#         ('o', 'other')
#     ]
#     sex = models.CharField(max_length=1, choices=SEX_CHOICES, default='o')
#     # collections
#
#     def __str__(self):
#         return self.user.username
#
#
# @receiver(post_save, sender=User)
# def create_custom_user(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)
#
#
# @receiver(post_save, sender=User)
# def save_custom_user(sender, instance, **kwargs):
#     instance.userprofile.save()
#
#
# @receiver(models.signals.pre_save, sender=UserProfile)
# def delete_file_on_change_extension(sender, instance, ** kwargs):
#     if instance.pk:
#         try:
#             old_avatar = UserProfile.objects.get(pk=instance.pk).profile_pic
#         except Exception as e:
#             return
#         new_avatar = instance.profile_pic
#         if new_avatar:
#             if old_avatar and old_avatar.url != new_avatar.url:
#                 old_avatar.delete(save=False)
#         else:
#             old_avatar.delete(save=False)

