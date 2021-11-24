from django.contrib import admin
from django.urls import path, include
from api.views import Hello, ListUsers

auth_urls = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]


urlpatterns = [
    path('', Hello.as_view(), name='hello-view'),
    path('', include(auth_urls)),
    # path('a/', ListUsers.as_view())
]
