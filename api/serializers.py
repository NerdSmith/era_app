from djoser.serializers import UserCreateSerializer
from .models import User
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
