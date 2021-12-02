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
            'id',
            'username',
            'password',
            'email',
            'profile_pic',
            'first_name',
            'last_name',
            'description',
            'location',
            'instagram_url',
            'vk_url',
            'sex',
        )


class UserShortSerializer(serializers.ModelSerializer):
    profile_pic = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile_pic',
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


class PhotoSeriesRetrieveSerializer(serializers.ModelSerializer):
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


class CollectionRetrieveSerializer(serializers.ModelSerializer):
    # collection_series = PhotoSeriesGetSerializer(many=True)

    class Meta:
        model = Collection
        fields = ['id', 'name', 'cover', 'description', 'owner', 'is_secret', 'created_at', 'collections_series']


class CollectionSerializer(serializers.ModelSerializer):
    # collection_series = PhotoSeriesGetSerializer(many=True)

    def create(self, validated_data):
        request = self.context.get('request', None)
        new_collection = Collection.objects.create(**validated_data, owner=request.user)
        return new_collection

    class Meta:
        model = Collection
        fields = ['id', 'name', 'cover', 'description', 'is_secret']


class PhotoSeriesSerializer(serializers.ModelSerializer):
    # series_photo = serializers.ListSerializer(child=serializers.ImageField())
    # tag = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    # tag = serializers.ListField(child=serializers.CharField())

    def create(self, validated_data):
        request = self.context.get('request', None)
        series_photo = request.data.getlist("series_photos")

        photo_series = PhotoSeries.objects.create(
            name=validated_data.get('name'),
            description=validated_data.get('description'),
            owner=request.user,
            price=validated_data.get('price'),
        )

        for tag_pk in validated_data.get('tag'):
            photo_series.tag.add(tag_pk)

        for i in range(len(series_photo)):
            SinglePhoto.objects.create(series=photo_series, order=i, photo=series_photo[i], owner=request.user)

        return photo_series


    class Meta:
        model = PhotoSeries
        fields = ['id', 'name', 'tag', 'description', 'price']
