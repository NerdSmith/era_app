from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .models import User, Tag, SinglePhoto, PhotoSeries, Collection


class SinglePhotoInLine(admin.TabularInline):
    model = SinglePhoto
    classes = ['collapse', ]
    # max_num = 1
    extra = 1
    show_change_link = True


# class UserProfileAdmin(admin.ModelAdmin):
#     # inlines = (SinglePhotoInLine, )
#     # list_display = ('user_email', )
#     list_display = ('user', )
#     fields = (
#         "user",
#         "subscribers",
#         "description",
#         "location",
#         'instagram_url',
#         'vk_url',
#         'sex',
#         'profile_pic',
#         'avatar_img'
#     )
#     readonly_fields = ['user', 'avatar_img']
#     filter_horizontal = ('subscribers', )
#     # search_fields = ('subscriber', )
#
#     def user_email(self, instance):
#         return instance.user.email
#
#     def avatar_img(self, obj):
#         return mark_safe('<img src="{url}" style="max-height:400px;height:100%" />'.format(
#             url=obj.profile_pic.url,
#             width=obj.profile_pic.width,
#             height=obj.profile_pic.height,
#             )
#         )
#
#
# admin.site.unregister(User)
# admin.site.unregister(Group)
# admin.site.register(User, UserAdmin)
# admin.site.register(UserProfile, UserProfileAdmin)


class SinglePhotoAdmin(admin.ModelAdmin):
    model = SinglePhoto
    readonly_fields = ("is_secret", "img")

    def img(self, obj):
        return mark_safe('<img src="{url}" style="max-height:400px;height:100%" />'.format(
            url=obj.photo.url,
            width=obj.photo.width,
            height=obj.photo.height,
            )
        )


class PhotoSeriesTagsInLine(admin.TabularInline):
    model = PhotoSeries.tag.through
    classes = ['collapse', ]
    show_change_link = True


class TagAdmin(admin.ModelAdmin):
    inlines = (PhotoSeriesTagsInLine, )


admin.site.register(Tag, TagAdmin)


class PhotoSeriesAdmin(admin.ModelAdmin):
    inlines = (SinglePhotoInLine, )
    readonly_fields = ("is_secret", )
    filter_horizontal = ('tag', )


class PhotoSeriesInLine(admin.TabularInline):
    model = PhotoSeries
    classes = ['collapse', ]
    extra = 1
    show_change_link = True


class CollectionAdmin(admin.ModelAdmin):
    inlines = (PhotoSeriesInLine, )
    fields = ('name', 'cover', 'cover_img', 'description', 'is_secret', 'owner', 'created_at')
    readonly_fields = ("cover_img", )

    def cover_img(self, obj):
        return mark_safe('<img src="{url}" style="max-height:400px;height:100%" />'.format(
            url=obj.cover.url,
            width=obj.cover.width,
            height=obj.cover.height,
            )
        )


class CollectionInLine(admin.TabularInline):
    model = Collection
    classes = ['collapse', ]
    extra = 1
    show_change_link = True


admin.site.register(SinglePhoto, SinglePhotoAdmin)
admin.site.register(PhotoSeries, PhotoSeriesAdmin)
admin.site.register(Collection, CollectionAdmin)


class UserAdmin(admin.ModelAdmin):
    inlines = (PhotoSeriesInLine, CollectionInLine)
    fieldsets = (
        (None, {
            'fields': ('username', 'first_name', 'last_name', 'email')
        }),
        ("System info", {
            'classes': ('collapse',),
            'fields': ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'groups', 'user_permissions')
        }),
        ("Profile info", {
            'classes': ('collapse',),
            'fields': ('subscribers', 'profile_pic', 'avatar_img', 'check_mark', 'description', 'location', 'instagram_url', 'vk_url', 'sex')
        })
    )
    readonly_fields = ['avatar_img', ]
    filter_horizontal = ('subscribers', )

    def avatar_img(self, obj):
        return mark_safe('<img src="{url}" style="max-height:400px;height:100%" />'.format(
            url=obj.profile_pic.url,
            width=obj.profile_pic.width,
            height=obj.profile_pic.height,
            )
        )


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
