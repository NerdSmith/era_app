from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Group
from django.utils.safestring import mark_safe

from .models import UserProfile, SinglePhoto, Tag, PhotoSeries, Collection


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'user profile'


class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'is_active', 'is_staff', 'is_superuser']
    inlines = (UserProfileInline,)


class SinglePhotoInLine(admin.TabularInline):
    model = SinglePhoto
    max_num = 1



class UserProfileAdmin(admin.ModelAdmin):
    # inlines = (SinglePhotoInLine, )
    # list_display = ('user_email', )
    list_display = ('user', )
    fields = (
        "user",
        "subscribers",
        "description",
        "location",
        'instagram_url',
        'vk_url',
        'sex',
        'profile_pic',
        'avatar_img'
    )
    readonly_fields = ['user', 'avatar_img']
    filter_horizontal = ('subscribers', )
    # search_fields = ('subscriber', )

    def user_email(self, instance):
        return instance.user.email

    def avatar_img(self, obj):
        return mark_safe('<img src="{url}" style="max-height:400px;height:100%" />'.format(
            url=obj.profile_pic.url,
            width=obj.profile_pic.width,
            height=obj.profile_pic.height,
            )
        )


admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)


class SinglePhotoAdmin(admin.ModelAdmin):
    model = SinglePhoto
    readonly_fields = ("is_secret", )


class PhotoSeriesTagsInLine(admin.TabularInline):
    model = PhotoSeries.tag.through


class TagAdmin(admin.ModelAdmin):
    inlines = (PhotoSeriesTagsInLine, )


admin.site.register(Tag, TagAdmin)


class PhotoSeriesAdmin(admin.ModelAdmin):
    inlines = (SinglePhotoInLine, )
    readonly_fields = ("is_secret", )


class PhotoSeriesInLine(admin.TabularInline):
    model = PhotoSeries
    extra = 1


class CollectionAdmin(admin.ModelAdmin):
    inlines = (PhotoSeriesInLine, )


admin.site.register(SinglePhoto, SinglePhotoAdmin)
admin.site.register(PhotoSeries, PhotoSeriesAdmin)
admin.site.register(Collection, CollectionAdmin)
