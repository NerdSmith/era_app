from random import sample, shuffle, choice, randint

from django.http import HttpResponse, Http404
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.response import Response

from rest_framework.views import APIView

from .models import Tag, PhotoSeries, Collection
from .permissions import IsOwnerOrStuff, IsNotSecret
from .serializers import PhotoSeriesGetSerializer, TagSerializer, PhotoSeriesShortSerializer, CollectionSerializer

User = get_user_model()


# Media view tunnel
class MediaAccess(APIView):
    permission_classes = [IsOwnerOrStuff | IsNotSecret]

    def get(self, request, format=None, path=None):
        response = HttpResponse()
        print(path)
        del response['Content-Type']
        response['X-Accel-Redirect'] = '/protected/media/' + path
        return response

# @
# def F(request):
#     pass

# PhotoSeries views
class PhotoSeriesView(APIView):
    permission_classes = [IsOwnerOrStuff | IsNotSecret]

    # def post(self, request, format=None):
    #     print(request.data)
    #     serializer = PhotoSeriesGetSerializer(data=request.data, context={'request': request})
    #     print('asdasd')
    #     print(serializer.is_valid())
    #     print(serializer.errors)
    #     article_saved = serializer.save()
    #     return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk, format=None):
        photo_series = PhotoSeries.objects.get(pk=pk)
        serializer = PhotoSeriesGetSerializer(photo_series)
        if not request.query_params:
            return Response(serializer.data) # single post
        else:
            related_tags = list(photo_series.tag.all())
            if related_tags:
                series = list(
                    PhotoSeries.objects.filter(
                        Q(
                            Q(collection__is_secret=False) | Q(collection__isnull=True)
                        ) & Q(tag=choice(related_tags))
                    )
                )
            else:
                series = list(
                    PhotoSeries.objects.filter(
                        Q(collection__is_secret=False) | Q(collection__isnull=True)
                    )
                )

            paginator = LimitOffsetPagination()
            paginator.default_limit = 5

            random_items = sample(series, min(paginator.default_limit, len(series)))
            result_page = paginator.paginate_queryset(random_items, request)
            serializer = PhotoSeriesShortSerializer(result_page, many=True)
            return Response(serializer.data) # recommendations for post


class PhotoSeriesMainPageView(APIView):
    # permission_classes = [IsNotSecret] # nn?

    def get(self, request, format=None): # add params for tag?
        series = PhotoSeries.objects.filter(Q(collection__is_secret=False) | Q(collection__isnull=True))
        if request.query_params:
            tags = request.query_params.getlist("tag_id")
            for tag in tags:
                series = series.filter(tag__id=int(tag))

        series = list(series)
        paginator = PageNumberPagination()
        # paginator.default_limit = 10
        paginator.page_size = 10

        # random_items = sample(series, min(paginator.page_size, len(series)))
        shuffle(series)
        result_page = paginator.paginate_queryset(series, request)
        serializer = PhotoSeriesShortSerializer(result_page, many=True)
        return Response(serializer.data)


# Collection views
class CollectionView(APIView):
    permission_classes = [IsOwnerOrStuff | IsNotSecret] # add req obj secret assertion

    def get(self, request, pk, format=None):
        collection = Collection.objects.get(pk=pk)
        serializer = CollectionSerializer(collection)
        return Response(serializer.data)


# Notification views
class NotificationView(APIView):
    def get(self, request, format=None):
        return HttpResponse("<h1>ABOBA</h1>")


# Tags Views
class TagView(APIView):
    def get_object(self, pk):
        try:
            return Tag.objects.get(pk=pk)
        except Tag.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        tag = self.get_object(pk)
        serializer = TagSerializer(tag)
        return Response(serializer.data)


class TagListView(APIView):
    def get(self, request, format=None):
        tag = Tag.objects.all()
        serializer = TagSerializer(tag, many=True)
        return Response(serializer.data)
