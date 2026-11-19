"""Public read-only API of the content app (`/api/content/`)."""

from django.core.paginator import Paginator
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import generics, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.views import PublicAPIMixin
from apps.content import selectors
from apps.content.models import SiteSettings
from apps.content.serializers import (
    AlbumDetailSerializer,
    AlbumListSerializer,
    ArticleDetailSerializer,
    ArticleListSerializer,
    FeedPhotoSerializer,
    HomeSerializer,
    NewsDetailSerializer,
    NewsListSerializer,
    PageSerializer,
    SiteSettingsSerializer,
    UsefulLinkSerializer,
)


class ContentPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 48


class SiteSettingsView(PublicAPIMixin, APIView):
    """Public site settings: name, contacts, links and the page background."""

    @extend_schema(responses=SiteSettingsSerializer)
    def get(self, request: Request) -> Response:
        settings = SiteSettings.get_solo()
        return Response(SiteSettingsSerializer(settings, context={"request": request}).data)


class HomeView(PublicAPIMixin, APIView):
    """Welcome text, home photo, latest news, featured varieties and latest articles."""

    @extend_schema(responses=HomeSerializer)
    def get(self, request: Request) -> Response:
        settings = SiteSettings.get_solo()
        content = selectors.home_content()
        data = {
            "welcome": settings.welcome,
            "hero_image": request.build_absolute_uri(settings.hero.url)
            if settings.hero_image
            else None,
            "latest_news": content.latest_news,
            "featured_varieties": content.featured_varieties,
            "latest_articles": content.latest_articles,
        }
        return Response(HomeSerializer(data, context={"request": request}).data)


class NewsListView(PublicAPIMixin, generics.ListAPIView):
    serializer_class = NewsListSerializer
    pagination_class = ContentPagination

    def get_queryset(self):
        return selectors.news_list()


class NewsDetailView(PublicAPIMixin, generics.RetrieveAPIView):
    serializer_class = NewsDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return selectors.news_list()


class ArticleListView(PublicAPIMixin, generics.ListAPIView):
    serializer_class = ArticleListSerializer
    pagination_class = ContentPagination

    def get_queryset(self):
        return selectors.article_list()


class ArticleDetailView(PublicAPIMixin, generics.RetrieveAPIView):
    serializer_class = ArticleDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return selectors.article_detail_queryset()


class UsefulLinkListView(PublicAPIMixin, generics.ListAPIView):
    serializer_class = UsefulLinkSerializer
    pagination_class = None

    def get_queryset(self):
        return selectors.useful_links()


class PageDetailView(PublicAPIMixin, generics.RetrieveAPIView):
    serializer_class = PageSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return selectors.pages()


class AlbumListView(PublicAPIMixin, generics.ListAPIView):
    serializer_class = AlbumListSerializer
    pagination_class = None

    def get_queryset(self):
        return selectors.album_list()


class AlbumDetailView(PublicAPIMixin, generics.RetrieveAPIView):
    serializer_class = AlbumDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return selectors.album_detail_queryset()


FEED_PAGE_SIZE = 24


class PhotoFeedView(PublicAPIMixin, APIView):
    """All photos (albums first, then varieties), newest first, for the infinite gallery."""

    @extend_schema(
        parameters=[OpenApiParameter("page", int, description="Page number, from 1.")],
        responses=inline_serializer(
            name="PaginatedFeedPhotoList",
            fields={
                "count": serializers.IntegerField(),
                "next_page": serializers.IntegerField(allow_null=True),
                "results": FeedPhotoSerializer(many=True),
            },
        ),
    )
    def get(self, request: Request) -> Response:
        paginator = Paginator(selectors.photo_feed_refs(), FEED_PAGE_SIZE)
        try:
            number = max(1, int(request.query_params.get("page", 1)))
        except ValueError:
            number = 1
        if number > paginator.num_pages:
            refs: list = []
            next_page = None
        else:
            page = paginator.page(number)
            refs = list(page.object_list)
            next_page = page.next_page_number() if page.has_next() else None
        photos = selectors.load_feed_photos(refs)
        return Response(
            {
                "count": paginator.count,
                "next_page": next_page,
                "results": FeedPhotoSerializer(
                    photos, many=True, context={"request": request}
                ).data,
            }
        )
