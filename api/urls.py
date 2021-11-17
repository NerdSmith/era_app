from django.contrib import admin
from django.urls import path, include
from api.views import Hello

urlpatterns = [
    path('', Hello.as_view(), name='hello-view')
]
