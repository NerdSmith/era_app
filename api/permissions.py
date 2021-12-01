from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.shortcuts import get_object_or_404

from .models import SinglePhoto, PhotoSeries, Collection


class IsOwnerOrStuff(BasePermission):
    def has_permission(self, request, view):
        curr_user = request.user
        if not curr_user.is_authenticated:
            print('not authenticated')
            return False
        elif curr_user.is_staff:
            print('stuff')
            return True

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user.is_staff


class IsNotSecret(BasePermission): # add req obj secret assertion
    def has_permission(self, request, view):
        url = view.kwargs.get("path")

        single_photo_obj = SinglePhoto.objects.filter(photo=url).first()
        if single_photo_obj:
            return single_photo_obj.owner == request.user or not single_photo_obj.is_secret()

        collection_obj = Collection.objects.filter(cover=url).first()
        if collection_obj:
            print(collection_obj.owner, request.user)
            return collection_obj.owner == request.user or not collection_obj.is_secret

        return True

    def has_object_permission(self, request, view, obj):
        return obj.is_secret


class CurrentUserOrAdminOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if type(obj) == type(user) and obj == user:
            return True
        return request.method in SAFE_METHODS or user.is_staff
