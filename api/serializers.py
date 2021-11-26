from djoser.serializers import UserCreateSerializer
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField

from .models import User, SinglePhoto, PhotoSeries, Tag, Collection
from rest_framework import serializers


class UserCreateSerializer(UserCreateSerializer):
    profile_pic = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'username',
            'password',
            'email',
            'profile_pic',
            'first_name',
            'last_name',
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'tag']


class SinglePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SinglePhoto
        fields = ['id', 'photo', 'order']


class SinglePhotoShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = SinglePhoto
        fields = ['photo', ]


class PhotoSeriesGetSerializer(serializers.ModelSerializer):
    series_photos = SinglePhotoSerializer(many=True)
    # series_photos = serializers.ImageField(many=True)
    # series_photos = SerializerMethodField('_series_photos')
    tag = TagSerializer(many=True, read_only=True)
    # tag = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = PhotoSeries
        fields = ['id', 'name', 'owner', 'tag', 'description', 'collection', 'created_at', 'price', 'series_photos']

    # def create(self, validated_data):
    #     print('val_data', validated_data)
    #     # photos_data = validated_data.pop('series_photos')
    #     # print('ph_data', photos_data)
    #     request = self.context.get('request', None)
    #     user = None
    #     if request.user:
    #         user = request.user
    #     photo_series = PhotoSeries.objects.create(
    #         name=validated_data.get('name'),
    #         description=validated_data.get('description'),
    #         owner=user,
    #         # collection,
    #         price=validated_data.get('price'),
    #     )
    #     photo_series.save()
    #     for tag_pk in validated_data.get('tag'):
    #         curr_tag = Tag.objects.get(pk=tag_pk)
    #         photo_series.tag.add(curr_tag)
    #
    #     # for i in range(len(photos_data)):
    #     #     SinglePhoto.objects.create(series=photo_series, order=i, **(photos_data[i]))
    #     #
    #     # for photo_data in photos_data:
    #     #     SinglePhoto.objects.create(album=photo_series, **photo_data)
    #     return photo_series


class PhotoSeriesShortSerializer(serializers.ModelSerializer):
    series_photos = SinglePhotoShortSerializer(many=True)

    class Meta:
        model = PhotoSeries
        fields = ['id', 'name', 'series_photos']


class CollectionSerializer(serializers.ModelSerializer):
    collection_series = PhotoSeriesGetSerializer(many=True)

    class Meta:
        model = Collection
        fields = ['id', 'name', 'cover', 'description', 'owner', 'is_secret', 'created_at', 'collection_series']
