from random import sample, shuffle, choice, randint

from django.http import HttpResponse, Http404, JsonResponse
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.views import View
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.response import Response

from rest_framework.views import APIView

from .models import Tag, PhotoSeries, Collection
from .permissions import IsOwnerOrStuff, IsNotSecret
from .serializers import PhotoSeriesRetrieveSerializer, TagSerializer, PhotoSeriesShortSerializer, \
    CollectionRetrieveSerializer, \
    PhotoSeriesSerializer, CollectionSerializer, UserShortSerializer

import requests

User = get_user_model()


class Hello(APIView):
    @swagger_auto_schema(
        operation_description="Возвращает html Hello, World!",
        operation_summary="Hello, World!",
        tags=['api test']
    )
    def get(self, request, *args, **kwargs):
        return HttpResponse('Hello, World!')

    @swagger_auto_schema(
        operation_description="Возвращает переданные параметры",
        operation_summary="Переданные параметры",
        request_body=openapi.Schema(
            title='Params',
            type=openapi.TYPE_OBJECT,
            properties={
                'param1': openapi.Schema(type=openapi.TYPE_STRING),
                'param2': openapi.Schema(type=openapi.TYPE_STRING),
                'param3': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        tags=['api test']
    )
    def post(self, request, format=None):
        print(request.data)
        return JsonResponse(request.data)


# Media view tunnel
class MediaAccess(APIView):
    permission_classes = [IsOwnerOrStuff | IsNotSecret]

    @swagger_auto_schema(
        operation_description="Возвращает фотографию по защищенному пути",
        operation_summary="Ссылка на фото",
        tags=['Media']
    )
    def get(self, request, format=None, path=None):
        response = HttpResponse()
        print(path)
        del response['Content-Type']
        response['X-Accel-Redirect'] = '/protected/media/' + path
        return response


# PhotoSeries views
class PhotoSeriesView(APIView):
    permission_classes = [IsOwnerOrStuff | IsNotSecret]

    @swagger_auto_schema(
        operation_description="Возвращает серию фото по её id, если запрос без параметров запроса, с параметрами "
                              "возвращает рекомендации по данному посту(берется 1 рандомный тег)",
        operation_summary="Серия фото",
        tags=['PhotoSeries'],
        manual_parameters=[
            openapi.Parameter(
                'id',
                description='id серии фото',
                in_=openapi.IN_PATH,
                required=True,
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                'limit',
                description='Максимальное количество обэктов',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                'offset',
                description='Отступ с начала обэктов',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: openapi.Response(
                'Серия фото',
                schema=PhotoSeriesRetrieveSerializer
            ),
            207: openapi.Response(
                'Рекомендации к фото',
                schema=PhotoSeriesShortSerializer(many=True)
            ),
            404: 'Серия фото не найдена не найдена'
        }
    )
    def get(self, request, pk, format=None):
        try:
            photo_series = PhotoSeries.objects.get(pk=pk)
            serializer = PhotoSeriesRetrieveSerializer(photo_series)
        except Exception as e:
            raise Http404
        if not request.query_params:
            return Response(serializer.data, status=status.HTTP_200_OK) # single post
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
            return Response(serializer.data, status=status.HTTP_207_MULTI_STATUS) # recommendations for post

    @swagger_auto_schema(
        operation_description="Удаляет серию фото по её id",
        operation_summary="Серия фото",
        tags=['PhotoSeries'],
        manual_parameters=[
            openapi.Parameter(
                'id',
                description='id серии фото',
                in_=openapi.IN_PATH,
                required=True,
                type=openapi.TYPE_INTEGER,
            )
        ],
        responses={
            204: 'Серия фото удалена',
            404: 'Серия фото не найдена',
            403: 'Доступ запрещен'
        }
    )
    def delete(self, request, pk, format=None):
        try:
            series = PhotoSeries.objects.get(pk=pk)
            print(series)
        except Exception as e:
            raise Http404
        if request.user == series.owner or request.user.is_staff:
            series.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


class PhotoSeriesCreateView(APIView):
    permission_classes = [IsAuthenticated, ]
    # parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        operation_description="Создание серии фото",
        operation_summary="Серия фото",
        tags=['PhotoSeries'],
        manual_parameters=[
            openapi.Parameter(
                'id',
                description='id серии фото',
                in_=openapi.IN_PATH,
                required=True,
                type=openapi.TYPE_INTEGER,
            ),

        ],
        request_body=openapi.Schema(
            'PhotoSeries',
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'tag': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        description='id тега',
                        type=openapi.TYPE_STRING
                    )
                ),
                'series_photos[]': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        description='файл фото',
                        type=openapi.TYPE_FILE
                    )
                ),
            }
        ),
        responses={
            201: PhotoSeriesSerializer,
            400: 'Плохой запрос'
        }
    )
    def post(self, request, format=None):
        print("post req: ", request.data)
        if request.data.getlist("series_photos[]"):
            serializer = PhotoSeriesSerializer(data=request.data, context={'request': request, })
            if serializer.is_valid():
                serializer.save()
                # return Response(status=status.HTTP_201_CREATED)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                # return Response(status=status.HTTP_200_OK)
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            # return Response(status=status.HTTP_200_OK)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # return Response(status=status.HTTP_200_OK)


class PhotoSeriesMainPageView(APIView):
    # permission_classes = [IsNotSecret] # nn?

    @swagger_auto_schema(
        operation_description="Возвращает главную страницу/главную страницу по заданным тегам",
        operation_summary="Главная страница",
        tags=['Main Page'],
        manual_parameters=[
            openapi.Parameter(
                'page',
                description='Номер страницы',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                'tag_id',
                description='Список тегов',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_INTEGER
                )
            ),
            openapi.Parameter(
                'search_query',
                description='Поисковый запрос',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
            )
        ],
        responses={
            200: openapi.Response(
                'Главная страница фото',
                schema=PhotoSeriesShortSerializer(many=True)
            ),
            # 404: 'Серия фото не найдена'
        }
    )
    def get(self, request, format=None):
        series = PhotoSeries.objects.filter(Q(collection__is_secret=False) | Q(collection__isnull=True))

        if request.query_params:
            tags = request.query_params.getlist("tag_id")
            if tags:
                tags = tags[0].split(',')
                for tag in tags:
                    series = series.filter(tag__id=int(tag))

            search_query = request.query_params.getlist("search_query")
            if search_query:
                for search in search_query:
                    series = series.filter(name__icontains=search)

        series = list(series)
        paginator = PageNumberPagination()
        paginator.page_size = 10

        shuffle(series)
        result_page = paginator.paginate_queryset(series, request)
        serializer = PhotoSeriesShortSerializer(result_page, many=True)
        return Response(serializer.data)


# Collection views
class CollectionView(APIView):
    permission_classes = [IsOwnerOrStuff | IsNotSecret] # add req obj secret assertion

    @swagger_auto_schema(
        operation_description="Возвращает коллекцию по её id",
        operation_summary="Коллекция",
        tags=['Collections'],
        manual_parameters=[
            openapi.Parameter(
                'id',
                description='id коллекции',
                in_=openapi.IN_PATH,
                required=True,
                type=openapi.TYPE_INTEGER,
            )
        ],
        responses={
            200: openapi.Response(
                'Коллекция',
                schema=CollectionRetrieveSerializer
                # openapi.Schema(
                #     'Collection',
                #     type=openapi.TYPE_OBJECT,
                #     properties={
                #         'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                #         'name': openapi.Schema(type=openapi.TYPE_STRING),
                #         'cover': openapi.Schema(type=openapi.TYPE_STRING),
                #         'description': openapi.Schema(type=openapi.TYPE_STRING),
                #         'owner': openapi.Schema(type=openapi.TYPE_INTEGER, description='id хозяина'),
                #         'is_secret': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                #         'created_at': openapi.Schema(
                #             type=openapi.TYPE_STRING,
                #             description='Время в формате типа 2021-11-27T21:33:50+03:00'
                #         ),
                #         'collections_series': openapi.Schema(
                #             type=openapi.TYPE_ARRAY,
                #             items=openapi.Schema(
                #                 description='id серий фото',
                #                 type=openapi.TYPE_INTEGER
                #             )
                #         ),
                #     }
                # )
            ),
            404: 'Коллекция не найдена'
        }
    )
    def get(self, request, pk, format=None):
        try:
            collection = Collection.objects.get(pk=pk)
        except Exception as e:
            raise Http404
        serializer = CollectionRetrieveSerializer(collection)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Удаляет коллекцию по её id",
        operation_summary="Коллекция",
        tags=['Collections'],
        manual_parameters=[
            openapi.Parameter(
                'id',
                description='id коллекции',
                in_=openapi.IN_PATH,
                required=True,
                type=openapi.TYPE_INTEGER,
            )
        ],
        responses={
            204: 'Коллекция удалена',
            404: 'Коллекция не найдена',
            403: 'Доступ запрещен'
        }
    )
    def delete(self, request, pk, format=None):
        try:
            collection = Collection.objects.get(pk=pk)
        except Exception as e:
            raise Http404
        if request.user == collection.owner or request.user.is_staff:
            collection.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    @swagger_auto_schema(
        operation_description="Возвращает коллекцию по её id",
        operation_summary="Коллекция",
        tags=['Collections'],
        manual_parameters=[
            openapi.Parameter(
                'id',
                description='id коллекции',
                in_=openapi.IN_PATH,
                required=True,
                type=openapi.TYPE_INTEGER,
            ),
        ],
        request_body=openapi.Schema(
            'series',
            type=openapi.TYPE_OBJECT,
            properties={
                'series_id': openapi.Schema(
                    description='id серии',
                    in_=openapi.IN_BODY,
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER))
            },
        ),
        responses={
            200: 'Серия добавлена',
            404: 'Коллекция не найдена',
            403: 'Доступ запрещен'
        }
    )
    def patch(self, request, pk, format=None):
        try:
            collection = Collection.objects.get(pk=pk)
        except Exception as e:
            raise Http404
        print(request.data)
        if request.user == collection.owner or request.user.is_staff:
            series_ids = request.data.get("series_id")
            print(series_ids)
            if series_ids:
            #     for series_id in series_ids:
            #         collection.collections_series.add(series_id)
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


class CollectionCreateView(APIView):
    permission_classes = [IsAuthenticated, ]
    parser_classes = (MultiPartParser, )

    @swagger_auto_schema(
        operation_description="Создает коллекцию",
        operation_summary="Коллекция",
        tags=['Collections'],
        request_body=CollectionSerializer,
        responses={
            201: CollectionSerializer,
            404: 'Коллекция не найдена',
            403: 'Доступ запрещен'
        }
    )
    def post(self, request, format=None):
        serializer = CollectionSerializer(data=request.data, context={'request': request, })
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


# Notification views
class NotificationView(APIView):
    @swagger_auto_schema(
        operation_description="ABOBA",
        operation_summary="ABOBA",
        tags=['Aboba']
    )
    def get(self, request, format=None):
        return HttpResponse("<h1>ABOBA</h1>")


# Tags Views
class TagView(APIView):
    def get_object(self, pk):
        try:
            return Tag.objects.get(pk=pk)
        except Tag.DoesNotExist:
            raise Http404

    @swagger_auto_schema(
        operation_description="Возвращает тег по его id",
        operation_summary="Тег",
        tags=['Tags'],
        manual_parameters=[
            openapi.Parameter(
                'id',
                description='id тега',
                in_=openapi.IN_PATH,
                required=True,
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: TagSerializer,
            404: 'Тег не найден'
        }
    )
    def get(self, request, pk, format=None):
        tag = self.get_object(pk)
        serializer = TagSerializer(tag)
        return Response(serializer.data)


class TagListView(APIView):
    @swagger_auto_schema(
        operation_description="Возвращает список тегов",
        operation_summary="Тег",
        tags=['Tags'],
        manual_parameters=[
            openapi.Parameter(
                'limit',
                description='Максимальное количество обэктов',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                'offset',
                description='Отступ с начала обэктов',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: TagSerializer,
            404: 'Тег не найден'
        }
    )
    def get(self, request, format=None):
        tag = Tag.objects.all().order_by('id')

        paginator = LimitOffsetPagination()
        paginator.default_limit = 5

        result_page = paginator.paginate_queryset(tag, request)

        serializer = TagSerializer(result_page, many=True)
        return Response(serializer.data)


# User views
class UserPhotoSeries(APIView):
    @swagger_auto_schema(
        operation_description="Возвращает серии фото пользователя",
        operation_summary="Фото пользователя",
        tags=['User', "PhotoSeries"],
        manual_parameters=[
            openapi.Parameter(
                'user_pk',
                description='id юзера',
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                'page',
                description='Номер страницы',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: openapi.Response(
                'Фото пользователя',
                schema=PhotoSeriesShortSerializer(many=True)
            ),
            404: 'Юзер не найден'
        }
    )
    def get(self, request, user_pk, format=None):
        try:
            user_photo_series = PhotoSeries.objects.filter(owner__id=user_pk).order_by('created_at')
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if request.user.id != user_pk:
            user_photo_series = user_photo_series.filter(Q(collection__is_secret=False) | Q(collection__isnull=True))

        paginator = PageNumberPagination()
        paginator.page_size = 9

        result_page = paginator.paginate_queryset(user_photo_series, request)

        serializer = PhotoSeriesShortSerializer(result_page, many=True)
        return Response(serializer.data)


class UserCollections(APIView):
    @swagger_auto_schema(
        operation_description="Возвращает коллекции пользователя",
        operation_summary="Коллекции пользователя",
        tags=['User', "Collections"],
        manual_parameters=[
            openapi.Parameter(
                'user_pk',
                description='id юзера',
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                'page',
                description='Номер страницы',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: openapi.Response(
                'Фото пользователя',
                schema=PhotoSeriesShortSerializer(many=True)
            ),
            404: 'Юзер не найден'
        }
    )
    def get(self, request, user_pk, format=None):
        try:
            user_collections = Collection.objects.filter(owner__id=user_pk).order_by('created_at')
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if request.user.id != user_pk:
            user_collections = user_collections.filter(is_secret=False)

        paginator = PageNumberPagination()
        paginator.page_size = 10

        result_page = paginator.paginate_queryset(user_collections, request)

        serializer = CollectionSerializer(result_page, many=True)
        return Response(serializer.data)


class UserSubscribeView(APIView):
    permission_classes = [IsAuthenticated, ]
    @swagger_auto_schema(
        operation_description="Подписывает на пользователя по его id",
        operation_summary="Субскрибшн",
        tags=['User', 'Subscription'],
        manual_parameters=[
            openapi.Parameter(
                'user_pk',
                description='id пользователя',
                in_=openapi.IN_PATH,
                required=True,
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: 'Подписан',
            400: 'Плохой запрос',
            403: 'Отказано в доступе',
        }
    )
    def post(self, request, user_pk, format=None):
        try:
            user_for_subscribe = User.objects.get(pk=user_pk)
        except Exception as e:
            raise Http404
        if user_for_subscribe != request.user:
            user_for_subscribe.subscribers.add(request.user.pk)
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    @swagger_auto_schema(
        operation_description="Отписывает пользователя по его id",
        operation_summary="Субскрибшн",
        tags=['User', 'Subscription'],
        manual_parameters=[
            openapi.Parameter(
                'user_pk',
                description='id пользователя',
                in_=openapi.IN_PATH,
                required=True,
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            204: 'Отписан',
            400: 'Плохой запрос',
            403: 'Отказано в доступе',
        }
    )
    def delete(self, request, user_pk, format=None):
        try:
            user_for_unsubscribe = User.objects.get(pk=user_pk)
        except Exception as e:
            raise Http404
        if user_for_unsubscribe != request.user:
            user_for_unsubscribe.subscribers.remove(request.user.pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


class UserSubscribersView(APIView):
    @swagger_auto_schema(
        operation_description="Возвращает количество подписок и количество подписчиков пользователя",
        operation_summary="Подписки и подписчики пользователя",
        tags=['User', "Subscription"],
        manual_parameters=[
            openapi.Parameter(
                'user_pk',
                description='id юзера',
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: openapi.Schema(
                'Информация о подписках',
                type=openapi.TYPE_OBJECT,
                properties={
                    "subscribers": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "subscribed_to": openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            ),
            404: 'Юзер не найден'
        }
    )
    def get(self, request, user_pk, format=None):
        try:
            user_subscribers = User.objects.get(pk=user_pk)
        except Exception as e:
            raise Http404
        subscribers_count = user_subscribers.subscribers.count()
        subscribed_to_count = user_subscribers.subscribed_to.count()
        return JsonResponse({"subscribers": subscribers_count, "subscribed_to": subscribed_to_count})


class UserShortInfo(APIView):
    @swagger_auto_schema(
        operation_description="Возвращает короткую информацию о пользователе",
        operation_summary="Пользователь",
        tags=['User', ],
        manual_parameters=[
            openapi.Parameter(
                'user_pk',
                description='id юзера',
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            200: UserShortSerializer,
            404: 'Юзер не найден'
        }
    )
    def get(self, request, user_pk, format=None):
        try:
            user = User.objects.get(pk=user_pk)
        except Exception as e:
            raise Http404
        serializer = UserShortSerializer(user)
        return Response(serializer.data)


class UserActivationView(APIView):
    def get(self, request, uid, token):
        protocol = 'https://' if request.is_secure() else 'http://'
        print(protocol)
        web_url = protocol + request.get_host()
        post_url = web_url + "/api/auth/users/activation/"
        print(post_url)
        post_data = {'uid': uid, 'token': token}
        result = requests.post(post_url, data=post_data)
        content = result.text
        return Response(content)

#
# class UserPasswordResetView(View):
#
#     def get(self, request, uid, token):
#         print('render', uid, token)
#         return render(request, 'reset_password.html')
#
#     def post(self, request, uid, token):
#         password = request.POST.get('password1')
#         payload = {'uid': uid, 'token': token, 'new_password': password}
#
#         url = '{0}://{1}{2}'.format(
#             django_settings.PROTOCOL, django_settings.DOMAIN, reverse('password_reset_confirm'))
#
#         response = requests.post(url, data=payload)
#         if response.status_code == 204:
#             # Give some feedback to the user. For instance:
#             # https://docs.djangoproject.com/en/2.2/ref/contrib/messages/
#             messages.success(request, 'Your password has been reset successfully!')
#             return redirect('home')
#         else:
#             return Response(response.json())
#
