from django.http import HttpResponse
from django.contrib.auth import get_user_model

# Create your views here.
from django.views import View
from rest_framework.response import Response

from rest_framework.views import APIView

User = get_user_model()


class Hello(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse('Hello, World!')


class ListUsers(APIView):

    def get(self, request, format=None):
        print(request.user)
        print(request.user.is_authenticated)
        usernames = [user.username for user in User.objects.all()]
        return Response(usernames)
