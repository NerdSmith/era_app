from django.urls import path, include

from api.views import PhotoSeriesView, TagView, TagListView, PhotoSeriesMainPageView, NotificationView, CollectionView, \
    Hello, PhotoSeriesCreateView, CollectionCreateView, UserPhotoSeries, UserCollections, UserSubscribeView, \
    UserSubscribersView

auth_urls = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]


urlpatterns = [
    path('', include(auth_urls)),

    path('categories/', TagListView.as_view()),
    path('categories/<int:pk>', TagView.as_view()),

    path('post/<int:pk>', PhotoSeriesView.as_view()),
    path('post/', PhotoSeriesCreateView.as_view()),
    path('photostock/', PhotoSeriesMainPageView.as_view()),

    path('collection/<int:pk>', CollectionView.as_view()),
    path('collection/', CollectionCreateView.as_view()),

    path('userposts/<int:user_pk>', UserPhotoSeries.as_view()),
    path('usercollections/<int:user_pk>', UserCollections.as_view()),
    path('user/subscribe/<int:user_pk>', UserSubscribeView.as_view()),
    path('user/subscribers/<int:user_pk>', UserSubscribersView.as_view()),

    path('notification/', NotificationView.as_view()),
    path('', Hello.as_view())
]
